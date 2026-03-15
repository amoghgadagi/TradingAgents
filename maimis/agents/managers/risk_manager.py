from __future__ import annotations

from maimis.models import AgentSignal


class RiskManager:
    def assess(self, signals: list[AgentSignal]) -> str:
        avg_conf = sum(s.confidence for s in signals) / max(len(signals), 1)
        regime = "high conviction" if avg_conf > 0.7 else "moderate/uncertain"
        return f"Risk manager: avg_confidence={avg_conf:.2f}, regime={regime}"
