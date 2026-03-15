from __future__ import annotations

from datetime import datetime

import pandas as pd
import yfinance as yf


def fetch_ohlcv(symbol: str, interval: str, period: str | None, start: datetime | None, end: datetime | None) -> pd.DataFrame:
    kwargs = {
        "tickers": symbol,
        "interval": interval,
        "auto_adjust": False,
        "progress": False,
        "threads": False,
    }
    if start or end:
        kwargs["start"] = start
        kwargs["end"] = end
    elif period:
        kwargs["period"] = period

    data = yf.download(**kwargs)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    cols = [c for c in ["Open", "High", "Low", "Close", "Volume"] if c in data.columns]
    out = data[cols].dropna(how="any")
    if out.empty:
        raise RuntimeError(f"Yahoo returned no OHLCV for {symbol}")
    return out
