from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentSignal:
    agent: str
    summary: str
    direction: str
    score: float
    confidence: float
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class DebateReview:
    agent: str
    verdict: str
    confidence_adjustment: float
    notes: str


@dataclass
class StrategyPlan:
    symbol: str
    market_bias: str
    confidence: float
    entry: float
    stop_loss: float
    targets: list[float]
    expected_holding: str
    rationale: str
    signals: list[AgentSignal]
    latest_price: float
    data_source: str
    data_period: str
    data_interval: str
    news_headlines: list[str] = field(default_factory=list)
