from __future__ import annotations

from collections.abc import Callable

from maimis.agents.debater_agent import DebaterAgent
from maimis.agents.macro_agent import MacroeconomicAgent
from maimis.agents.managers.research_manager import ResearchManager
from maimis.agents.managers.risk_manager import RiskManager
from maimis.agents.order_flow_agent import OrderFlowAgent
from maimis.agents.quant_agent import QuantAgent
from maimis.agents.researchers_core import BearResearcherAgent, BullResearcherAgent
from maimis.agents.sentiment_agent import SentimentAgent
from maimis.agents.strategy_agent import StrategyAgent
from maimis.agents.technical_agent import TechnicalIndicatorsAgent
from maimis.agents.volume_agent import VolumeAnalysisAgent
from maimis.agents.chart_agent import ChartAnalysisAgent
from maimis.dataflows import MAIMISDataProvider
from maimis.models import AgentSignal, StrategyPlan


class MAIMISTradingGraph:
    def __init__(self) -> None:
        self.provider = MAIMISDataProvider()
        self.chart_agent = ChartAnalysisAgent()
        self.volume_agent = VolumeAnalysisAgent()
        self.technical_agent = TechnicalIndicatorsAgent()
        self.order_flow_agent = OrderFlowAgent()
        self.sentiment_agent = SentimentAgent()
        self.macro_agent = MacroeconomicAgent()
        self.quant_agent = QuantAgent()
        self.debater = DebaterAgent()
        self.bull_researcher = BullResearcherAgent()
        self.bear_researcher = BearResearcherAgent()
        self.research_manager = ResearchManager()
        self.risk_manager = RiskManager()
        self.strategy_agent = StrategyAgent()

    def run(
        self,
        symbol: str,
        interval: str,
        days: int | None = None,
        period: str = "5d",
        start_date: str | None = None,
        end_date: str | None = None,
        require_live: bool = False,
        on_step: Callable[[str, str], None] | None = None,
    ) -> tuple[dict, StrategyPlan]:
        def emit(step: str, status: str) -> None:
            if on_step:
                on_step(step, status)

        emit("data_collection", "in_progress")
        data = self.provider.fetch(
            symbol=symbol,
            interval=interval,
            days=days,
            period=period,
            start_date=start_date,
            end_date=end_date,
            require_live=require_live,
        )
        emit("data_collection", "completed")

        raw_signals: list[AgentSignal] = []
        for step, fn, arg in [
            ("chart_agent", self.chart_agent.run, data.ohlcv),
            ("volume_agent", self.volume_agent.run, data.ohlcv),
            ("technical_agent", self.technical_agent.run, data.ohlcv),
            ("order_flow_agent", self.order_flow_agent.run, data.ohlcv),
            ("sentiment_agent", self.sentiment_agent.run, data.news),
            ("macro_agent", self.macro_agent.run, data.macro),
            ("quant_agent", self.quant_agent.run, data.ohlcv),
        ]:
            emit(step, "in_progress")
            sig = fn(arg)
            review = self.debater.review(sig)
            sig.confidence = max(0.1, min(0.99, sig.confidence + review.confidence_adjustment))
            sig.details["debate_verdict"] = review.verdict
            sig.details["debate_notes"] = review.notes
            raw_signals.append(sig)
            emit(step, "completed")

        emit("research_manager", "in_progress")
        research_summary = self.research_manager.summarize(raw_signals)
        emit("research_manager", "completed")

        emit("bull_researcher", "in_progress")
        bull = self.bull_researcher.run(raw_signals)
        emit("bull_researcher", "completed")

        emit("bear_researcher", "in_progress")
        bear = self.bear_researcher.run(raw_signals)
        emit("bear_researcher", "completed")

        emit("risk_manager", "in_progress")
        risk_summary = self.risk_manager.assess(raw_signals + [bull, bear])
        emit("risk_manager", "completed")

        emit("trader_agent", "in_progress")
        plan = self.strategy_agent.run(
            symbol=symbol,
            ohlcv=data.ohlcv,
            signals=raw_signals,
            bull=bull,
            bear=bear,
            data_source=data.source,
            data_period=(f"{days}d" if days is not None else period),
            data_interval=interval,
            news_headlines=[n.get("title", "") for n in data.news if n.get("title")],
        )
        emit("trader_agent", "completed")

        state = {
            "source": data.source,
            "research_summary": research_summary,
            "risk_summary": risk_summary,
            "news": data.news,
            "ohlcv": data.ohlcv,
            "signals": raw_signals,
        }
        return state, plan
