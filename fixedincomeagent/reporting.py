"""Reusable report-tree writer shared by the CLI and the programmatic API.

Writes a run's per-section markdown (analysts, research, trading, risk,
portfolio) plus a consolidated ``complete_report.md`` under ``save_path``. The
CLI and ``TradingAgentsGraph.save_reports`` both call this, so a headless / API
run produces the same on-disk report tree a CLI run does.
"""

from datetime import datetime
from pathlib import Path


def write_report_tree(final_state: dict, ticker: str, save_path) -> Path:
    """Save a completed run's reports to ``save_path``; return the complete-report path."""
    save_path = Path(save_path)
    save_path.mkdir(parents=True, exist_ok=True)
    sections = []

    # 1. Analysts
    analysts_dir = save_path / "1_analysts"
    analyst_parts = []
    analyst_keys = [
        ("macro_policy_report", "Macro Policy Analyst"),
        ("curve_technicals_report", "Curve Technicals Analyst"),
        ("fed_speak_report", "Fed Speak Analyst"),
        ("macro_calendar_report", "Macro Calendar Analyst"),
        ("market_report", "Market Analyst"),
        ("sentiment_report", "Sentiment Analyst"),
        ("news_report", "News Analyst"),
        ("fundamentals_report", "Fundamentals Analyst"),
    ]
    for rkey, rname in analyst_keys:
        if final_state.get(rkey):
            analysts_dir.mkdir(exist_ok=True)
            fname = rkey.replace("_report", "") + ".md"
            (analysts_dir / fname).write_text(final_state[rkey], encoding="utf-8")
            analyst_parts.append((rname, final_state[rkey]))

    if analyst_parts:
        content = "\n\n".join(f"### {name}\n{text}" for name, text in analyst_parts)
        sections.append(f"## I. Analyst Team Reports\n\n{content}")

    # 2. Research & Debates
    research_dir = save_path / "2_research"
    research_parts = []

    # FI Direction Debate
    if final_state.get("direction_debate_state"):
        dir_debate = final_state["direction_debate_state"]
        if dir_debate.get("higher_yields_history"):
            research_dir.mkdir(exist_ok=True)
            (research_dir / "direction_higher.md").write_text(dir_debate["higher_yields_history"], encoding="utf-8")
            research_parts.append(("Higher Yields Researcher", dir_debate["higher_yields_history"]))
        if dir_debate.get("lower_yields_history"):
            research_dir.mkdir(exist_ok=True)
            (research_dir / "direction_lower.md").write_text(dir_debate["lower_yields_history"], encoding="utf-8")
            research_parts.append(("Lower Yields Researcher", dir_debate["lower_yields_history"]))
        if dir_debate.get("judge_decision"):
            research_dir.mkdir(exist_ok=True)
            (research_dir / "direction_manager.md").write_text(dir_debate["judge_decision"], encoding="utf-8")
            research_parts.append(("Direction Research Manager", dir_debate["judge_decision"]))

    # FI Shape Debate
    if final_state.get("shape_debate_state"):
        shape_debate = final_state["shape_debate_state"]
        if shape_debate.get("steepener_history"):
            research_dir.mkdir(exist_ok=True)
            (research_dir / "shape_steepener.md").write_text(shape_debate["steepener_history"], encoding="utf-8")
            research_parts.append(("Steepener Researcher", shape_debate["steepener_history"]))
        if shape_debate.get("flattener_history"):
            research_dir.mkdir(exist_ok=True)
            (research_dir / "shape_flattener.md").write_text(shape_debate["flattener_history"], encoding="utf-8")
            research_parts.append(("Flattener Researcher", shape_debate["flattener_history"]))
        if shape_debate.get("judge_decision"):
            research_dir.mkdir(exist_ok=True)
            (research_dir / "shape_manager.md").write_text(shape_debate["judge_decision"], encoding="utf-8")
            research_parts.append(("Shape Research Manager", shape_debate["judge_decision"]))

    # Equity Research Debate
    if final_state.get("investment_debate_state"):
        debate = final_state["investment_debate_state"]
        if debate.get("bull_history"):
            research_dir.mkdir(exist_ok=True)
            (research_dir / "bull.md").write_text(debate["bull_history"], encoding="utf-8")
            research_parts.append(("Bull Researcher", debate["bull_history"]))
        if debate.get("bear_history"):
            research_dir.mkdir(exist_ok=True)
            (research_dir / "bear.md").write_text(debate["bear_history"], encoding="utf-8")
            research_parts.append(("Bear Researcher", debate["bear_history"]))
        if debate.get("judge_decision"):
            research_dir.mkdir(exist_ok=True)
            (research_dir / "manager.md").write_text(debate["judge_decision"], encoding="utf-8")
            research_parts.append(("Research Manager", debate["judge_decision"]))

    if research_parts:
        content = "\n\n".join(f"### {name}\n{text}" for name, text in research_parts)
        sections.append(f"## II. Research Team Decision\n\n{content}")

    # 3. Trading
    if final_state.get("trader_investment_plan"):
        trading_dir = save_path / "3_trading"
        trading_dir.mkdir(exist_ok=True)
        (trading_dir / "trader.md").write_text(final_state["trader_investment_plan"], encoding="utf-8")
        sections.append(f"## III. Trading Team Plan\n\n### Trader\n{final_state['trader_investment_plan']}")

    # 4. Risk Management (Equity)
    if final_state.get("risk_debate_state"):
        risk_dir = save_path / "4_risk"
        risk = final_state["risk_debate_state"]
        risk_parts = []
        if risk.get("aggressive_history"):
            risk_dir.mkdir(exist_ok=True)
            (risk_dir / "aggressive.md").write_text(risk["aggressive_history"], encoding="utf-8")
            risk_parts.append(("Aggressive Analyst", risk["aggressive_history"]))
        if risk.get("conservative_history"):
            risk_dir.mkdir(exist_ok=True)
            (risk_dir / "conservative.md").write_text(risk["conservative_history"], encoding="utf-8")
            risk_parts.append(("Conservative Analyst", risk["conservative_history"]))
        if risk.get("neutral_history"):
            risk_dir.mkdir(exist_ok=True)
            (risk_dir / "neutral.md").write_text(risk["neutral_history"], encoding="utf-8")
            risk_parts.append(("Neutral Analyst", risk["neutral_history"]))
        if risk_parts:
            content = "\n\n".join(f"### {name}\n{text}" for name, text in risk_parts)
            sections.append(f"## IV. Risk Management Team Decision\n\n{content}")

        # 5. Portfolio Manager
        if risk.get("judge_decision"):
            portfolio_dir = save_path / "5_portfolio"
            portfolio_dir.mkdir(exist_ok=True)
            (portfolio_dir / "decision.md").write_text(risk["judge_decision"], encoding="utf-8")
            sections.append(f"## V. Portfolio Manager Decision\n\n### Portfolio Manager\n{risk['judge_decision']}")

    # 5. FI Portfolio Manager Decision (when final_trade_decision exists without risk_debate_state)
    if final_state.get("final_trade_decision") and not final_state.get("risk_debate_state"):
        portfolio_dir = save_path / "5_portfolio"
        portfolio_dir.mkdir(exist_ok=True)
        (portfolio_dir / "decision.md").write_text(final_state["final_trade_decision"], encoding="utf-8")
        sections.append(f"## V. Portfolio Manager Decision\n\n### FI Portfolio Manager\n{final_state['final_trade_decision']}")

    # Write consolidated report
    header = f"# Trading Analysis Report: {ticker}\n\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    (save_path / "complete_report.md").write_text(header + "\n\n".join(sections), encoding="utf-8")
    return save_path / "complete_report.md"
