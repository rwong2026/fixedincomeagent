# FixedIncomeAgent/graph/reflection.py

from typing import Any

from ..agents.utils.argument_tagger import TaggedArgument, tag_debate_arguments


class Reflector:
    """Handles reflection on trading decisions."""

    def __init__(self, quick_thinking_llm: Any):
        """Initialize the reflector with an LLM."""
        self.quick_thinking_llm = quick_thinking_llm
        self.log_reflection_prompt = self._get_log_reflection_prompt()
        self.fi_log_reflection_prompt = self._get_fi_log_reflection_prompt()

    def _get_log_reflection_prompt(self) -> str:
        """Concise prompt for reflect_on_final_decision (Phase B log entries).

        Produces 2-4 sentences of plain prose — compact enough to be re-injected
        into future agent prompts without bloating the context window.
        """
        return (
            "You are a trading analyst reviewing your own past decision now that the outcome is known.\n"
            "Write exactly 2-4 sentences of plain prose (no bullets, no headers, no markdown).\n\n"
            "Cover in order:\n"
            "1. Was the directional call correct? (cite the alpha figure)\n"
            "2. Which part of the investment thesis held or failed?\n"
            "3. One concrete lesson to apply to the next similar analysis.\n\n"
            "Be specific and terse. Your output will be stored verbatim in a decision log "
            "and re-read by future analysts, so every word must earn its place."
        )

    def _get_fi_log_reflection_prompt(self) -> str:
        """Concise prompt for reflect_on_fi_decision (Fixed Income Treasury curve).

        Produces 2-4 sentences of plain prose reviewing yield curve and rate calls
        against an equal-weight Treasury curve benchmark.
        """
        return (
            "You are a fixed-income trading analyst reviewing your own past US Treasury yield-curve "
            "decision now that the outcome is known.\n"
            "Write exactly 2-4 sentences of plain prose (no bullets, no headers, no markdown).\n\n"
            "Cover in order:\n"
            "1. Was the curve and directional call correct? (cite the hit rate and alpha vs the equal-weight curve benchmark)\n"
            "2. Which part of the macro/rate thesis (inflation, Fed speak, technicals) held or failed across tenors?\n"
            "3. One concrete lesson to apply to future curve positioning.\n\n"
            "Be specific and terse. Your output will be stored verbatim in a decision log "
            "and re-read by future analysts, so every word must earn its place."
        )

    def reflect_on_final_decision(
        self,
        final_decision: str,
        raw_return: float,
        alpha_return: float,
        benchmark_name: str = "SPY",
    ) -> str:
        """Single reflection call on the final trade decision with outcome context.

        Used by Phase B deferred reflection. The final_trade_decision already
        synthesises all analyst insights, so no separate market context is needed.
        ``benchmark_name`` is the label used for the alpha line (e.g. ``"SPY"``
        for US tickers, ``"^N225"`` for ``.T`` listings); defaults to SPY for
        callers that haven't been updated to thread the benchmark through.
        """
        messages = [
            ("system", self.log_reflection_prompt),
            (
                "human",
                (
                    f"Raw return: {raw_return:+.1%}\n"
                    f"Alpha vs {benchmark_name}: {alpha_return:+.1%}\n\n"
                    f"Final Decision:\n{final_decision}"
                ),
            ),
        ]
        return self.quick_thinking_llm.invoke(messages).content

    def reflect_on_fi_decision(
        self,
        final_decision: str,
        benchmark_bp: float,
        hit_rate: str,
        tenor_changes: dict[str, Any],
        alpha_bp: float = 0.0,
    ) -> str:
        """Single reflection call on an FI yield-curve decision with benchmark metrics."""
        tenor_lines = []
        for t, data in tenor_changes.items():
            delta = data.get("delta_bp", 0.0) if isinstance(data, dict) else float(data)
            tenor_lines.append(f"{t}: {delta:+.1f}bp")

        tenor_str = ", ".join(tenor_lines)
        messages = [
            ("system", self.fi_log_reflection_prompt),
            (
                "human",
                (
                    f"Hit rate: {hit_rate}\n"
                    f"Equal-weight curve benchmark yield change: {benchmark_bp:+.1f}bp\n"
                    f"Alpha vs benchmark: {alpha_bp:+.1f}bp\n"
                    f"Actual tenor yield changes: {tenor_str}\n\n"
                    f"Final Decision:\n{final_decision}"
                ),
            ),
        ]
        return self.quick_thinking_llm.invoke(messages).content

    def tag_debate_arguments(self, debate_history: str) -> list[TaggedArgument]:
        """SCAFFOLDING ONLY — opt-in, not called from any live graph path.

        Thin delegate to ``agents.utils.argument_tagger.tag_debate_arguments``.
        Activated only after Phase 7's backtest validates the baseline; until
        then nothing calls this and nothing changes about reflection behaviour.
        """
        return tag_debate_arguments(self.quick_thinking_llm, debate_history)
