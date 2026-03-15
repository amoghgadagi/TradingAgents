from __future__ import annotations

import pandas as pd

from maimis.models import AgentSignal


class VolumeAnalysisAgent:
    name = "volume_analysis"

    def run(self, ohlcv: pd.DataFrame) -> AgentSignal:
        volume = ohlcv["Volume"].tail(80)
        close = ohlcv["Close"].tail(80)

        avg_volume = float(volume.mean())
        last_volume = float(volume.iloc[-1])
        spike_ratio = last_volume / avg_volume if avg_volume else 1.0
        price_delta = float(close.iloc[-1] - close.iloc[-10]) if len(close) >= 10 else float(close.iloc[-1] - close.iloc[0])

        direction = "bullish" if price_delta >= 0 else "bearish"
        institutional_signal = spike_ratio > 1.8
        confidence = min(0.95, 0.5 + abs(spike_ratio - 1.0) * 0.4)
        score = min(0.95, 0.5 + (spike_ratio - 1.0) * 0.25)
        score = score if direction == "bullish" else 1.0 - score

        summary = (
            f"Volume spike ratio {spike_ratio:.2f} with {'institutional participation' if institutional_signal else 'normal flow'}, "
            f"price impulse {price_delta:.2f}."
        )

        return AgentSignal(
            agent=self.name,
            summary=summary,
            direction=direction,
            score=float(max(0.05, min(0.95, score))),
            confidence=float(confidence),
            details={
                "avg_volume": avg_volume,
                "last_volume": last_volume,
                "spike_ratio": spike_ratio,
                "institutional_signal": institutional_signal,
            },
        )
