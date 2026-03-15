from __future__ import annotations

from maimis.models import AgentSignal


class BullResearcherAgent:
    name = "bull_researcher"

    def run(self, signals: list[AgentSignal]) -> AgentSignal:
        bullish_scores = [s.score for s in signals if s.direction == "bullish"]
        bearish_scores = [1 - s.score for s in signals if s.direction == "bearish"]
        net = (sum(bullish_scores) + sum(bearish_scores)) / max(len(signals), 1)
        probability = max(0.05, min(0.95, net))
        confidence = 0.55 + abs(probability - 0.5)

        return AgentSignal(
            agent=self.name,
            summary=f"Bull thesis probability={probability:.1%} based on cross-agent alignment.",
            direction="bullish",
            score=float(probability),
            confidence=float(min(0.95, confidence)),
            details={"bullish_probability": probability},
        )


class BearResearcherAgent:
    name = "bear_researcher"

    def run(self, signals: list[AgentSignal]) -> AgentSignal:
        bear_prob = 1 - (sum(s.score for s in signals if s.direction == "bullish") / max(len(signals), 1))
        bear_prob = max(0.05, min(0.95, bear_prob))
        confidence = 0.55 + abs(bear_prob - 0.5)

        return AgentSignal(
            agent=self.name,
            summary=f"Bear thesis probability={bear_prob:.1%} from downside and risk signals.",
            direction="bearish",
            score=float(bear_prob),
            confidence=float(min(0.95, confidence)),
            details={"bearish_probability": bear_prob},
        )
