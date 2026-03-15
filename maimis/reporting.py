from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from maimis.dataflows.config import DEFAULT_OUTPUT_DIR
from maimis.models import AgentSignal, StrategyPlan


def _run_dir(base_dir: str | None = None) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    root = Path(base_dir or DEFAULT_OUTPUT_DIR) / ts
    root.mkdir(parents=True, exist_ok=True)
    (root / "agents").mkdir(parents=True, exist_ok=True)
    return root


def save_agent_reports(signals: list[AgentSignal], run_dir: Path) -> list[str]:
    paths: list[str] = []
    for s in signals:
        p = run_dir / "agents" / f"{s.agent}.md"
        lines = [
            f"# {s.agent}",
            "",
            f"- direction: **{s.direction}**",
            f"- score: **{s.score:.2f}**",
            f"- confidence: **{s.confidence:.2f}**",
            f"- summary: {s.summary}",
            "",
            "## details",
        ]
        for k, v in s.details.items():
            lines.append(f"- {k}: `{v}`")
        p.write_text("\n".join(lines))
        paths.append(str(p))
    return paths


def render_markdown_report(plan: StrategyPlan, research_summary: str = "", risk_summary: str = "") -> str:
    lines = [
        "# MAIMIS Trading Report",
        "",
        f"**Generated (UTC):** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Symbol:** {plan.symbol}",
        f"**Latest Price:** {plan.latest_price}",
        f"**Data Source:** {plan.data_source}",
        f"**Data Window:** {plan.data_period} @ {plan.data_interval}",
        "",
        "## Team Summaries",
        f"- Research Manager: {research_summary}",
        f"- Risk Manager: {risk_summary}",
        "",
        "## Final Strategy Decision",
        f"- Market Bias: **{plan.market_bias}**",
        f"- Confidence: **{plan.confidence:.1%}**",
        f"- Entry: **{plan.entry}**",
        f"- Stop Loss: **{plan.stop_loss}**",
        f"- Targets: **{', '.join(str(t) for t in plan.targets)}**",
        f"- Expected Holding: **{plan.expected_holding}**",
        f"- Rationale: {plan.rationale}",
        "",
        "## Headlines",
    ]
    if plan.news_headlines:
        lines.extend([f"- {h}" for h in plan.news_headlines[:10]])
    else:
        lines.append("- none")

    lines.extend(["", "## Agent Reports", "| Agent | Direction | Score | Confidence |", "|---|---:|---:|---:|"])
    for s in plan.signals:
        lines.append(f"| {s.agent} | {s.direction} | {s.score:.2f} | {s.confidence:.2f} |")
    return "\n".join(lines)


def save_run_outputs(
    plan: StrategyPlan,
    research_summary: str,
    risk_summary: str,
    report_path: str | None = None,
    output_dir: str | None = None,
) -> dict:
    run_dir = _run_dir(output_dir)
    final_report = render_markdown_report(plan, research_summary, risk_summary)
    final_path = Path(report_path) if report_path else run_dir / "final_report.md"
    final_path.parent.mkdir(parents=True, exist_ok=True)
    final_path.write_text(final_report)
    agent_paths = save_agent_reports(plan.signals, run_dir)
    return {"run_dir": str(run_dir), "final_report": str(final_path), "agent_reports": agent_paths}
