from __future__ import annotations

import pandas as pd

from maimis.agents.prompts import get_prompt
from maimis.models import AgentSignal


class TechnicalIndicatorsAgent:
    name = "technical_indicators"
    prompt = get_prompt(name)

    def run(self, ohlcv: pd.DataFrame) -> AgentSignal:
        close = ohlcv["Close"]
        high = ohlcv["High"]
        low = ohlcv["Low"]
        volume = ohlcv["Volume"]

        sma20 = close.rolling(20).mean().iloc[-1]
        sma50 = close.rolling(50).mean().iloc[-1]
        sma200 = close.rolling(200).mean().iloc[-1] if len(close) >= 200 else close.rolling(min(100, len(close))).mean().iloc[-1]
        ema9 = close.ewm(span=9, adjust=False).mean().iloc[-1]
        std20 = close.rolling(20).std().iloc[-1]
        upper = sma20 + (2 * std20)
        lower = sma20 - (2 * std20)

        delta = close.diff()
        up = delta.clip(lower=0).rolling(14).mean().iloc[-1]
        down = (-delta.clip(upper=0)).rolling(14).mean().iloc[-1]
        rs = up / down if down and down > 0 else 1.0
        rsi = 100 - (100 / (1 + rs))

        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        macd = float(macd_line.iloc[-1])

        typical = (high + low + close) / 3
        vwap = float((typical * volume).cumsum().iloc[-1] / volume.cumsum().iloc[-1])

        atr = float((high - low).rolling(14).mean().iloc[-1])
        stoch_k = float(((close - low.rolling(14).min()) / (high.rolling(14).max() - low.rolling(14).min() + 1e-9) * 100).iloc[-1])
        momentum_10 = float(close.pct_change(10).iloc[-1] * 100)
        roc_20 = float(close.pct_change(20).iloc[-1] * 100)

        breakout_high_20 = float(high.tail(20).max())
        breakdown_low_20 = float(low.tail(20).min())
        is_breakout = bool(close.iloc[-1] >= breakout_high_20)
        is_breakdown = bool(close.iloc[-1] <= breakdown_low_20)

        swing_high = float(high.tail(40).max())
        swing_low = float(low.tail(40).min())
        obv = float((volume * close.diff().fillna(0).apply(lambda x: 1 if x > 0 else -1 if x < 0 else 0)).cumsum().iloc[-1])

        bullish_votes = sum(
            [
                close.iloc[-1] > sma20,
                sma20 > sma50,
                sma50 > sma200,
                macd > float(signal_line.iloc[-1]),
                rsi < 70,
                close.iloc[-1] >= vwap,
                momentum_10 > 0,
            ]
        )
        direction = "bullish" if bullish_votes >= 4 else "bearish"
        score_raw = bullish_votes / 7
        score = score_raw if direction == "bullish" else 1 - score_raw
        confidence = 0.55 + abs(bullish_votes - 3.5) / 7

        market_state = "breakout" if is_breakout else "breakdown" if is_breakdown else "range/swing"
        summary = (
            f"State={market_state}, RSI={rsi:.1f}, MACD={macd:.3f}, MOM10={momentum_10:.2f}%, "
            f"price/SMA20/SMA50={close.iloc[-1]:.2f}/{sma20:.2f}/{sma50:.2f}."
        )

        return AgentSignal(
            agent=self.name,
            summary=summary,
            direction=direction,
            score=float(max(0.05, min(0.95, score))),
            confidence=float(min(0.95, confidence)),
            details={
                "analysis_prompt": self.prompt,
                "market_state": market_state,
                "rsi": float(rsi),
                "stoch_k": stoch_k,
                "macd": macd,
                "macd_signal": float(signal_line.iloc[-1]),
                "momentum_10_pct": momentum_10,
                "roc_20_pct": roc_20,
                "sma20": float(sma20),
                "sma50": float(sma50),
                "sma200": float(sma200),
                "ema9": float(ema9),
                "vwap": vwap,
                "atr14": atr,
                "bollinger_upper": float(upper),
                "bollinger_lower": float(lower),
                "breakout_high_20": breakout_high_20,
                "breakdown_low_20": breakdown_low_20,
                "swing_high_40": swing_high,
                "swing_low_40": swing_low,
                "obv": obv,
            },
        )
