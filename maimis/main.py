from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.table import Table

from maimis.graph import MAIMISTradingGraph
from maimis.reporting import save_run_outputs

app = typer.Typer(help="Run MAIMIS intraday multi-agent analysis locally.", no_args_is_help=True)
console = Console()


@app.callback()
def main() -> None:
    """MAIMIS CLI."""


@app.command("run")
def run(
    symbol: str = typer.Option("MES=F", help="Ticker symbol."),
    interval: str = typer.Option("5m", help="Bar interval, e.g. 1m, 5m, 15m, 1h, 1d."),
    days: int | None = typer.Option(None, help="Historical window in days (overrides period)."),
    period: str = typer.Option("5d", help="yfinance-style period if days not provided."),
    start_date: str | None = typer.Option(None, help="ISO start date/time."),
    end_date: str | None = typer.Option(None, help="ISO end date/time."),
    require_live: bool = typer.Option(False, help="Fail if AlphaVantage/Yahoo live pull both fail."),
    as_json: bool = typer.Option(False, help="Print machine-readable JSON output."),
    show_ohlcv: bool = typer.Option(False, help="Display OHLCV tail in terminal."),
    ohlcv_rows: int = typer.Option(8, help="Number of OHLCV tail rows to print."),
    save_ohlcv_csv: str | None = typer.Option(None, help="Optional CSV path for OHLCV."),
    report_path: str | None = typer.Option(None, help="Optional final report path."),
    output_dir: str | None = typer.Option(None, help="Output directory for per-agent reports."),
) -> None:
    graph = MAIMISTradingGraph()

    statuses = {
        "data_collection": "pending",
        "chart_agent": "pending",
        "volume_agent": "pending",
        "technical_agent": "pending",
        "order_flow_agent": "pending",
        "sentiment_agent": "pending",
        "macro_agent": "pending",
        "quant_agent": "pending",
        "research_manager": "pending",
        "bull_researcher": "pending",
        "bear_researcher": "pending",
        "risk_manager": "pending",
        "trader_agent": "pending",
    }

    def on_step(step: str, status: str) -> None:
        statuses[step] = status
        if not as_json:
            table = Table(title="MAIMIS Agent Workflow")
            table.add_column("Step")
            table.add_column("Status")
            for k, v in statuses.items():
                table.add_row(k, v)
            console.clear()
            console.print(table)
            console.print(f"symbol={symbol} | interval={interval} | days={days} | period={period} | start={start_date} | end={end_date}")

    try:
        state, plan = graph.run(
            symbol=symbol,
            interval=interval,
            days=days,
            period=period,
            start_date=start_date,
            end_date=end_date,
            require_live=require_live,
            on_step=on_step,
        )
    except RuntimeError as exc:
        typer.echo(f"[MAIMIS] ERROR: {exc}")
        raise typer.Exit(code=2)

    outputs = save_run_outputs(
        plan=plan,
        research_summary=state.get("research_summary", ""),
        risk_summary=state.get("risk_summary", ""),
        report_path=report_path,
        output_dir=output_dir,
    )

    if save_ohlcv_csv:
        state["ohlcv"].to_csv(save_ohlcv_csv)

    if as_json:
        payload = {
            **plan.__dict__,
            "source": state.get("source"),
            "research_summary": state.get("research_summary"),
            "risk_summary": state.get("risk_summary"),
            "output_paths": outputs,
            "news_count": len(state.get("news", [])),
            "ohlcv_tail": state["ohlcv"].tail(ohlcv_rows).reset_index().to_dict(orient="records"),
        }
        print(json.dumps(payload, default=lambda o: o.__dict__, indent=2))
        return

    console.print("\n[bold green]=== MAIMIS TRADER OUTPUT ===[/bold green]")
    console.print(f"Symbol: {plan.symbol}")
    console.print(f"Source: {state.get('source')} | Latest Price: {plan.latest_price}")
    console.print(f"Bias: {plan.market_bias} | Confidence: {plan.confidence:.0%}")
    console.print(f"Entry={plan.entry} Stop={plan.stop_loss} Targets={plan.targets}")
    console.print(f"Research Manager: {state.get('research_summary')}")
    console.print(f"Risk Manager: {state.get('risk_summary')}")
    console.print(f"Final report: {outputs['final_report']}")
    console.print(f"Agent reports dir: {outputs['run_dir']}/agents")

    if show_ohlcv:
        console.print(f"\nOHLCV tail ({ohlcv_rows} rows):")
        console.print(state["ohlcv"].tail(ohlcv_rows).to_string())

    if plan.news_headlines:
        console.print("\nTop headlines:")
        for h in plan.news_headlines[:5]:
            console.print(f"- {h}")


if __name__ == "__main__":
    app()
