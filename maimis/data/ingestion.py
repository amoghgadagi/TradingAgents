from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import logging

import numpy as np
import pandas as pd
import yfinance as yf


@dataclass
class MarketDataBundle:
    symbol: str
    ohlcv: pd.DataFrame
    news: list[dict]
    macro: dict[str, float]
    data_source: str


class YFinanceIngestion:
    """Fetches market OHLCV + news from Yahoo Finance with fallback support."""

    def __init__(self) -> None:
        logging.getLogger("yfinance").setLevel(logging.CRITICAL)
        logging.getLogger("curl_cffi").setLevel(logging.CRITICAL)

    def fetch(
        self,
        symbol: str = "MES=F",
        period: str = "5d",
        interval: str = "5m",
        days: int | None = None,
        end_date: str | None = None,
        require_live: bool = False,
    ) -> MarketDataBundle:
        try:
            download_kwargs: dict[str, object] = {
                "tickers": symbol,
                "interval": interval,
                "auto_adjust": False,
                "progress": False,
                "group_by": "column",
                "threads": False,
            }

            if days is not None:
                end_dt = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc) if end_date else datetime.now(timezone.utc)
                start_dt = end_dt - pd.Timedelta(days=days)
                download_kwargs["start"] = start_dt
                download_kwargs["end"] = end_dt
            elif end_date:
                end_dt = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)
                start_dt = end_dt - self._period_to_timedelta(period)
                download_kwargs["start"] = start_dt
                download_kwargs["end"] = end_dt
            else:
                download_kwargs["period"] = period

            ohlcv = yf.download(**download_kwargs)
            ohlcv = self._normalize_ohlcv(ohlcv)
            if ohlcv.empty:
                raise ValueError(
                    f"No OHLCV data returned for symbol={symbol}, period={period}, interval={interval}, days={days}, end_date={end_date}"
                )

            news = self._fetch_news(symbol)
            macro = self._fetch_macro_proxies()
            return MarketDataBundle(symbol=symbol, ohlcv=ohlcv, news=news, macro=macro, data_source="yfinance")
        except Exception as exc:
            if require_live:
                raise RuntimeError(
                    "Live Yahoo Finance pull failed. Retry in an environment with Yahoo access or disable --require-live."
                ) from exc
            return self._fallback_bundle(symbol=symbol)

    def _fetch_news(self, symbol: str) -> list[dict]:
        ticker = yf.Ticker(symbol)
        raw_news = ticker.news or []
        normalized: list[dict] = []
        for item in raw_news[:50]:
            content = item.get("content") or {}
            title = content.get("title") or item.get("title") or ""
            provider = content.get("provider") or item.get("publisher") or "unknown"
            link = content.get("canonicalUrl", {}).get("url") or item.get("link") or ""
            pub_time = content.get("pubDate") or item.get("providerPublishTime")
            if title:
                normalized.append(
                    {
                        "title": title,
                        "provider": provider,
                        "link": link,
                        "published_at": pub_time,
                    }
                )
        return normalized

    def _fetch_macro_proxies(self) -> dict[str, float]:
        return {
            "vix": self._safe_last_close("^VIX"),
            "tnx": self._safe_last_close("^TNX"),
            "dxy": self._safe_last_close("DX-Y.NYB"),
        }

    @staticmethod
    def _normalize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df

        if isinstance(df.columns, pd.MultiIndex):
            df = df.copy()
            if len(df.columns.levels) > 1:
                try:
                    df.columns = df.columns.get_level_values(0)
                except Exception:
                    pass

        expected = ["Open", "High", "Low", "Close", "Volume"]
        cols = [c for c in expected if c in df.columns]
        out = df[cols].copy()
        out = out.dropna(how="any")
        return out

    @staticmethod
    def _safe_last_close(symbol: str) -> float:
        data = yf.download(symbol, period="5d", interval="1d", progress=False, auto_adjust=False)
        data = YFinanceIngestion._normalize_ohlcv(data)
        if data.empty:
            return float("nan")
        return float(data["Close"].iloc[-1])

    @staticmethod
    def _fallback_bundle(symbol: str) -> MarketDataBundle:
        idx = pd.date_range(end=pd.Timestamp.utcnow(), periods=200, freq="5min")
        base = 5300 + np.cumsum(np.random.normal(0, 0.8, size=len(idx)))
        close = pd.Series(base, index=idx)
        open_ = close.shift(1).fillna(close.iloc[0])
        high = pd.concat([open_, close], axis=1).max(axis=1) + np.random.uniform(0.05, 0.6, size=len(idx))
        low = pd.concat([open_, close], axis=1).min(axis=1) - np.random.uniform(0.05, 0.6, size=len(idx))
        volume = np.random.randint(100, 1200, size=len(idx))

        ohlcv = pd.DataFrame(
            {
                "Open": open_.values,
                "High": high.values,
                "Low": low.values,
                "Close": close.values,
                "Volume": volume,
            },
            index=idx,
        )

        macro = {"vix": 19.5, "tnx": 4.2, "dxy": 103.5}
        news: list[dict] = []
        return MarketDataBundle(symbol=symbol, ohlcv=ohlcv, news=news, macro=macro, data_source="fallback")

    @staticmethod
    def _period_to_timedelta(period: str) -> pd.Timedelta:
        period = period.strip().lower()
        unit = period[-1]
        value = int(period[:-1])
        if unit == "d":
            return pd.Timedelta(days=value)
        if unit == "w":
            return pd.Timedelta(weeks=value)
        if unit == "m":
            return pd.Timedelta(days=30 * value)
        if unit == "y":
            return pd.Timedelta(days=365 * value)
        raise ValueError(f"Unsupported period format: {period}")
