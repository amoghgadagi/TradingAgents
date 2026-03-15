from __future__ import annotations

from maimis.agents.chart_agent import ChartAnalysisAgent
from maimis.agents.debater_agent import DebaterAgent
from maimis.agents.macro_agent import MacroeconomicAgent
from maimis.agents.order_flow_agent import OrderFlowAgent
from maimis.agents.quant_agent import QuantAgent
from maimis.agents.researchers_core import BearResearcherAgent, BullResearcherAgent
from maimis.agents.sentiment_agent import SentimentAgent
from maimis.agents.strategy_agent import StrategyAgent
from maimis.agents.technical_agent import TechnicalIndicatorsAgent
from maimis.agents.volume_agent import VolumeAnalysisAgent
from maimis.data.ingestion import MarketDataBundle, YFinanceIngestion
from maimis.models import StrategyPlan


class MAIMISPipeline:
    def __init__(self) -> None:
        self.ingestion = YFinanceIngestion()
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
        self.strategy_agent = StrategyAgent()

    def run(
        self,
        symbol: str = "MES=F",
        period: str = "5d",
        interval: str = "5m",
        days: int | None = None,
        end_date: str | None = None,
        require_live: bool = False,
        preloaded_data: MarketDataBundle | None = None,
    ) -> StrategyPlan:
        data = preloaded_data or self.ingestion.fetch(
            symbol=symbol,
            period=period,
            interval=interval,
            days=days,
            end_date=end_date,
            require_live=require_live,
        )

        raw_signals = [
            self.chart_agent.run(data.ohlcv),
            self.volume_agent.run(data.ohlcv),
            self.technical_agent.run(data.ohlcv),
            self.order_flow_agent.run(data.ohlcv),
            self.sentiment_agent.run(data.news),
            self.macro_agent.run(data.macro),
            self.quant_agent.run(data.ohlcv),
        ]

        validated = []
        for signal in raw_signals:
            review = self.debater.review(signal)
            signal.confidence = max(0.1, min(0.99, signal.confidence + review.confidence_adjustment))
            signal.details["debate_verdict"] = review.verdict
            signal.details["debate_notes"] = review.notes
            validated.append(signal)

        bull = self.bull_researcher.run(validated)
        bear = self.bear_researcher.run(validated)

        news_headlines = [n.get("title", "") for n in data.news if n.get("title")]

        return self.strategy_agent.run(
            symbol=symbol,
            ohlcv=data.ohlcv,
            signals=validated,
            bull=bull,
            bear=bear,
            data_source=data.data_source,
            data_period=(f"{days}d" if days is not None else period),
            data_interval=interval,
            news_headlines=news_headlines,
        )
