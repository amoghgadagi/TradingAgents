from __future__ import annotations

from datetime import datetime, timedelta

import yfinance as yf

from .alpha_vantage_news import fetch_news as fetch_av_news
from .alpha_vantage_stock import fetch_ohlcv as fetch_av_ohlcv
from .config import ALPHA_VANTAGE_API_KEY
from .interface import DataResult
from .yfinance_market import fetch_ohlcv as fetch_yf_ohlcv
from .yfinance_news import fetch_news as fetch_yf_news


class MAIMISDataProvider:
    def fetch(
        self,
        symbol: str,
        interval: str,
        days: int | None = None,
        period: str = "5d",
        start_date: str | None = None,
        end_date: str | None = None,
        require_live: bool = False,
    ) -> DataResult:
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        if days is not None and end_dt is None:
            end_dt = datetime.utcnow()
        if days is not None and start_dt is None and end_dt is not None:
            start_dt = end_dt - timedelta(days=days)

        errors: list[str] = []

        try:
            ohlcv = fetch_av_ohlcv(symbol=symbol, api_key=ALPHA_VANTAGE_API_KEY, interval=interval, start=start_dt, end=end_dt)
            news = fetch_av_news(symbol=symbol, api_key=ALPHA_VANTAGE_API_KEY)
            macro = self._macro()
            return DataResult(symbol=symbol, ohlcv=ohlcv, news=news, macro=macro, source="alpha_vantage")
        except Exception as exc:
            errors.append(f"alpha_vantage: {exc}")

        try:
            yf_period = None if (start_dt or end_dt) else period
            ohlcv = fetch_yf_ohlcv(symbol=symbol, interval=interval, period=yf_period, start=start_dt, end=end_dt)
            news = fetch_yf_news(symbol=symbol)
            macro = self._macro()
            return DataResult(symbol=symbol, ohlcv=ohlcv, news=news, macro=macro, source="yfinance")
        except Exception as exc:
            errors.append(f"yfinance: {exc}")

        if require_live:
            raise RuntimeError("Live data pull failed: " + " | ".join(errors))

        # fallback synthetic
        from maimis.data.ingestion import YFinanceIngestion

        fb = YFinanceIngestion._fallback_bundle(symbol)
        return DataResult(symbol=symbol, ohlcv=fb.ohlcv, news=fb.news, macro=fb.macro, source="fallback")

    @staticmethod
    def _macro() -> dict[str, float]:
        def last_close(sym: str) -> float:
            data = yf.download(sym, period="5d", interval="1d", progress=False, auto_adjust=False)
            if data.empty:
                return float("nan")
            if "Close" in data:
                return float(data["Close"].iloc[-1])
            if hasattr(data.columns, "levels"):
                return float(data["Close"].iloc[-1])
            return float("nan")

        return {"vix": last_close("^VIX"), "tnx": last_close("^TNX"), "dxy": last_close("DX-Y.NYB")}
