from __future__ import annotations

import pandas as pd

from maimis.agents.prompts import get_prompt
from maimis.models import AgentSignal


class QuantAgent:
    name = "quantitative"
    prompt = get_prompt(name)

    def run(self, ohlcv: pd.DataFrame) -> AgentSignal:
        close = ohlcv["Close"]
        returns = close.pct_change().dropna()

        vol = float(returns.tail(80).std() * (80 ** 0.5))
        momentum = float(close.iloc[-1] / close.iloc[-30] - 1) if len(close) > 30 else float(close.iloc[-1] / close.iloc[0] - 1)
        mean_reversion = float((close.iloc[-1] - close.tail(40).mean()) / max(close.tail(40).std(), 1e-6))

        directional_prob = 0.5 + (momentum * 5) - (mean_reversion * 0.05)
        directional_prob = max(0.05, min(0.95, directional_prob))

        direction = "bullish" if directional_prob >= 0.5 else "bearish"
        confidence = min(0.92, 0.55 + abs(directional_prob - 0.5) + min(vol, 0.2))
        score = directional_prob if direction == "bullish" else 1 - directional_prob

        summary = (
            f"Quant model momentum={momentum:.3%}, vol={vol:.3f}, z={mean_reversion:.2f}; "
            f"directional probability={directional_prob:.1%}."
        )

        return AgentSignal(
            agent=self.name,
            summary=summary,
            direction=direction,
            score=float(score),
            confidence=float(confidence),
            details={
                "analysis_prompt": self.prompt,
                "volatility": vol,
                "momentum": momentum,
                "mean_reversion_z": mean_reversion,
                "directional_probability": directional_prob,
            },
        )
