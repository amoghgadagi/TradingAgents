from __future__ import annotations

from maimis.models import AgentSignal, DebateReview


class DebaterAgent:
    """Simple validator that adjusts confidence based on internal consistency."""

    def review(self, signal: AgentSignal) -> DebateReview:
        verdict = "accepted"
        adjustment = 0.0
        notes = "Signal appears internally consistent."

        if signal.direction == "neutral":
            verdict = "accepted_with_caution"
            adjustment = -0.1
            notes = "Neutral signals carry lower directional value."
        elif signal.confidence < 0.5:
            verdict = "accepted_with_caution"
            adjustment = -0.08
            notes = "Low confidence; reduce impact in aggregation."
        elif signal.score > 0.9 or signal.score < 0.1:
            verdict = "challenged"
            adjustment = -0.05
            notes = "Extreme score detected; clipped influence to avoid overreaction."

        return DebateReview(
            agent=signal.agent,
            verdict=verdict,
            confidence_adjustment=adjustment,
            notes=notes,
        )
