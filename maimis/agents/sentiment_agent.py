from __future__ import annotations

from maimis.agents.prompts import get_prompt
from maimis.models import AgentSignal


class SentimentAgent:
    name = "sentiment"
    prompt = get_prompt(name)

    POSITIVE = {
        "beat", "surge", "strong", "growth", "upgrade", "bullish", "rally", "record", "cooling inflation"
    }
    NEGATIVE = {
        "miss", "drop", "weak", "downgrade", "bearish", "selloff", "recession", "hot inflation", "war"
    }

    def run(self, news: list[dict]) -> AgentSignal:
        headlines: list[str] = []
        for item in news[:30]:
            title = (item.get("title") or "").strip()
            if title:
                headlines.append(title)

        if not headlines:
            return AgentSignal(
                agent=self.name,
                summary="No recent Yahoo/AV headlines found; sentiment neutral by default.",
                direction="neutral",
                score=0.5,
                confidence=0.35,
                details={
                    "analysis_prompt": self.prompt,
                    "headlines": 0,
                    "top_headlines": [],
                },
            )

        lower = [h.lower() for h in headlines]
        pos = sum(sum(word in h for word in self.POSITIVE) for h in lower)
        neg = sum(sum(word in h for word in self.NEGATIVE) for h in lower)
        raw = pos - neg
        normalized = max(-1.0, min(1.0, raw / max(len(headlines), 1)))

        direction = "bullish" if normalized > 0.05 else "bearish" if normalized < -0.05 else "neutral"
        score = 0.5 + (normalized / 2)
        confidence = min(0.85, 0.4 + len(headlines) / 50)

        return AgentSignal(
            agent=self.name,
            summary=f"News sentiment from {len(headlines)} headlines: pos={pos}, neg={neg}, bias={direction}.",
            direction=direction,
            score=float(max(0.05, min(0.95, score))),
            confidence=float(confidence),
            details={
                "analysis_prompt": self.prompt,
                "positive_hits": pos,
                "negative_hits": neg,
                "headlines": len(headlines),
                "top_headlines": headlines[:5],
            },
        )
