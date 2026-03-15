from __future__ import annotations

import pandas as pd

from maimis.models import AgentSignal, StrategyPlan


class StrategyAgent:
    name = "strategy"

    def run(
        self,
        symbol: str,
        ohlcv: pd.DataFrame,
        signals: list[AgentSignal],
        bull: AgentSignal,
        bear: AgentSignal,
        data_source: str,
        data_period: str,
        data_interval: str,
        news_headlines: list[str],
    ) -> StrategyPlan:
        last = float(ohlcv["Close"].iloc[-1])
        atr_proxy = float((ohlcv["High"].tail(30) - ohlcv["Low"].tail(30)).mean())

        directional_score = bull.score - bear.score
        market_bias = "Bullish" if directional_score >= 0 else "Bearish"
        confidence = min(0.95, 0.5 + abs(directional_score))

        if market_bias == "Bullish":
            entry = last
            stop = entry - 1.2 * atr_proxy
            targets = [entry + atr_proxy, entry + 2 * atr_proxy, entry + 3 * atr_proxy]
            rationale = "Breakout continuation favored by aggregate bullish evidence."
        else:
            entry = last
            stop = entry + 1.2 * atr_proxy
            targets = [entry - atr_proxy, entry - 2 * atr_proxy, entry - 3 * atr_proxy]
            rationale = "Breakdown continuation favored by aggregate bearish evidence."

        return StrategyPlan(
            symbol=symbol,
            market_bias=market_bias,
            confidence=float(confidence),
            entry=round(entry, 2),
            stop_loss=round(stop, 2),
            targets=[round(t, 2) for t in targets],
            expected_holding="30-240 minutes",
            rationale=rationale,
            signals=signals + [bull, bear],
            latest_price=round(last, 2),
            data_source=data_source,
            data_period=data_period,
            data_interval=data_interval,
            news_headlines=news_headlines[:10],
        )
