from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class DataResult:
    symbol: str
    ohlcv: pd.DataFrame
    news: list[dict]
    macro: dict[str, float]
    source: str
