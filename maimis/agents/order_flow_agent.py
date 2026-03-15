from __future__ import annotations

import pandas as pd

from maimis.models import AgentSignal


class OrderFlowAgent:
    """Approximates microstructure from candle-level proxy metrics (yfinance has no L2 book)."""

    name = "order_flow"

    def run(self, ohlcv: pd.DataFrame) -> AgentSignal:
        recent = ohlcv.tail(40).copy()
        spread_proxy = (recent["High"] - recent["Low"]).replace(0, 1e-6)
        body = recent["Close"] - recent["Open"]
        imbalance = float((body / spread_proxy).mean())
        pressure = float((body * recent["Volume"]).sum() / max(recent["Volume"].sum(), 1))

        direction = "bullish" if pressure >= 0 else "bearish"
        confidence = min(0.92, 0.52 + abs(imbalance) * 0.5)
        score = 0.5 + max(min(imbalance, 0.45), -0.45)
        score = score if direction == "bullish" else 1 - score

        summary = (
            f"Proxy flow imbalance={imbalance:.3f}, pressure={pressure:.3f}; "
            f"short-term {direction} pressure."
        )

        return AgentSignal(
            agent=self.name,
            summary=summary,
            direction=direction,
            score=float(max(0.05, min(0.95, score))),
            confidence=float(confidence),
            details={
                "imbalance": imbalance,
                "pressure": pressure,
            },
        )
