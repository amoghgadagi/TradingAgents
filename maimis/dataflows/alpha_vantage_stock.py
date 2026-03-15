from __future__ import annotations

from datetime import datetime

import pandas as pd

from .alpha_vantage_common import av_get


def fetch_ohlcv(symbol: str, api_key: str, interval: str, start: datetime | None, end: datetime | None) -> pd.DataFrame:
    if not api_key:
        raise ValueError("Missing ALPHA_VANTAGE_API_KEY")

    function = "TIME_SERIES_INTRADAY" if interval.endswith("min") else "TIME_SERIES_DAILY"
    params = {
        "function": function,
        "symbol": symbol,
        "apikey": api_key,
        "datatype": "json",
        "outputsize": "full",
    }
    if function == "TIME_SERIES_INTRADAY":
        params["interval"] = interval

    data = av_get(params)
    if "Note" in data or "Information" in data:
        raise RuntimeError(data.get("Note") or data.get("Information"))

    key = [k for k in data.keys() if "Time Series" in k]
    if not key:
        raise RuntimeError(f"Alpha Vantage OHLCV unavailable for {symbol}")

    ts = data[key[0]]
    rows = []
    for dt_str, vals in ts.items():
        dt = datetime.fromisoformat(dt_str)
        if start and dt < start:
            continue
        if end and dt > end:
            continue
        rows.append(
            {
                "Datetime": dt,
                "Open": float(vals.get("1. open", 0)),
                "High": float(vals.get("2. high", 0)),
                "Low": float(vals.get("3. low", 0)),
                "Close": float(vals.get("4. close", 0)),
                "Volume": float(vals.get("5. volume", 0)),
            }
        )

    if not rows:
        raise RuntimeError("Alpha Vantage returned no rows in requested range")

    df = pd.DataFrame(rows).sort_values("Datetime").set_index("Datetime")
    return df
