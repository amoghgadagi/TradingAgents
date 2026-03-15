from __future__ import annotations

from maimis.models import AgentSignal


class ResearchManager:
    def summarize(self, signals: list[AgentSignal]) -> str:
        bullish = sum(1 for s in signals if s.direction == "bullish")
        bearish = sum(1 for s in signals if s.direction == "bearish")
        return f"Research manager summary: bullish={bullish}, bearish={bearish}, total={len(signals)}"
