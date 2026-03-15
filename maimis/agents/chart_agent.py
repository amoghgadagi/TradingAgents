from __future__ import annotations

import numpy as np
import pandas as pd

from maimis.models import AgentSignal


class ChartAnalysisAgent:
    name = "chart_analysis"

    def run(self, ohlcv: pd.DataFrame) -> AgentSignal:
        close = ohlcv["Close"]
        recent = close.tail(60)
        trend_slope = float(np.polyfit(np.arange(len(recent)), recent.values, 1)[0])
        direction = "bullish" if trend_slope > 0 else "bearish"
        rolling_high = float(ohlcv["High"].tail(50).max())
        rolling_low = float(ohlcv["Low"].tail(50).min())
        breakout_prob = 0.5 + min(abs(trend_slope) / max(recent.std(), 1e-6), 0.45)
        score = breakout_prob if direction == "bullish" else 1 - breakout_prob
        confidence = min(0.95, 0.55 + abs(trend_slope) / max(recent.std(), 1e-6))

        summary = (
            f"{direction.title()} structure with slope={trend_slope:.3f}, "
            f"key range [{rolling_low:.2f}, {rolling_high:.2f}]"
        )

        return AgentSignal(
            agent=self.name,
            summary=summary,
            direction=direction,
            score=float(score),
            confidence=float(confidence),
            details={
                "support": rolling_low,
                "resistance": rolling_high,
                "breakout_probability": float(breakout_prob),
            },
        )
