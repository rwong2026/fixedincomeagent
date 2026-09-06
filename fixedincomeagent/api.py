"""Public programmatic API for FixedIncomeAgent.

Allows running Fixed Income (or equity dual-track) analyses headlessly
or streamed, suitable for CLI, web backends (e.g. FastAPI / Flask), or
automated pipelines without importing any CLI-specific terminal logic.
"""

from collections.abc import Generator, Iterable
from datetime import datetime
from pathlib import Path
from typing import Any

from fixedincomeagent.default_config import DEFAULT_CONFIG
from fixedincomeagent.graph.analyst_execution import FI_ANALYST_KEYS
from fixedincomeagent.graph.trading_graph import TradingAgentsGraph

DEFAULT_FI_ANALYSTS = (
    "macro_policy",
    "curve_technicals",
    "fed_speak",
    "macro_calendar",
)


class FixedIncomeAnalysis:
    """High-level API for orchestrating fixed-income (and dual-track) analysis."""

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        analysts: Iterable[str] | None = None,
        callbacks: list | None = None,
        debug: bool = False,
        disabled_tools: Iterable[str] | None = None,
    ):
        """Initialize the analysis orchestration.

        Args:
            config: Configuration dictionary (falls back to DEFAULT_CONFIG).
            analysts: Iterable of analyst keys to run. Defaults to the 4 FI analysts.
            callbacks: Optional LangChain / custom callbacks.
            debug: Whether to run underlying graph in debug mode.
            disabled_tools: Optional collection of tool names to exclude (ablation).
        """
        self.config = config or DEFAULT_CONFIG
        self.selected_analysts = tuple(analysts) if analysts is not None else DEFAULT_FI_ANALYSTS
        self.callbacks = callbacks or []
        self.debug = debug
        self.disabled_tools = disabled_tools

        self.graph = TradingAgentsGraph(
            selected_analysts=self.selected_analysts,
            debug=self.debug,
            config=self.config,
            callbacks=self.callbacks,
            disabled_tools=self.disabled_tools,
        )

    @property
    def fi_mode(self) -> bool:
        """Whether the selected analyst set triggers the FI graph track."""
        return bool(self.selected_analysts) and set(self.selected_analysts) <= FI_ANALYST_KEYS

    def run(
        self,
        label: str = "UST",
        trade_date: str | None = None,
        asset_type: str = "stock",
    ) -> dict[str, Any]:
        """Run complete analysis synchronously to completion.

        Returns a dictionary containing the final agent state and the portfolio signal.
        """
        if trade_date is None:
            trade_date = datetime.now().strftime("%Y-%m-%d")

        final_state, signal = self.graph.propagate(
            label,
            trade_date,
            asset_type=asset_type,
        )
        result = dict(final_state)
        result["signal"] = signal
        result["ticker"] = label
        result["trade_date"] = trade_date
        return result

    def run_streaming(
        self,
        label: str = "UST",
        trade_date: str | None = None,
        asset_type: str = "stock",
    ) -> Generator[dict[str, Any], None, None]:
        """Stream analysis chunk by chunk.

        Useful for live CLI updates, web sockets, or server-sent events (SSE).
        Yields graph stream chunks and manages the checkpointer lifecycle.
        """
        if trade_date is None:
            trade_date = datetime.now().strftime("%Y-%m-%d")

        # Resolve instrument context deterministic anchor
        instrument_context = self.graph.resolve_instrument_context(label, asset_type)

        init_agent_state = self.graph.propagator.create_initial_state(
            label,
            trade_date,
            asset_type=asset_type,
            instrument_context=instrument_context,
        )

        args = self.graph.propagator.get_graph_args(callbacks=self.callbacks)

        # Resolve pending memory entries before starting
        self.graph._resolve_pending_entries(label)

        checkpoint_tid = self.graph.begin_checkpoint(label, trade_date, asset_type)
        if checkpoint_tid is not None:
            args.setdefault("config", {}).setdefault("configurable", {})["thread_id"] = checkpoint_tid

        try:
            yield from self.graph.graph.stream(
                self.graph.checkpoint_input(init_agent_state), **args
            )

            self.graph.clear_checkpoint_on_success(label, trade_date, asset_type)
        finally:
            self.graph.end_checkpoint()

    def save_reports(
        self,
        final_state: dict[str, Any],
        label: str,
        save_path: str | Path | None = None,
    ) -> Path:
        """Write report markdown tree to disk."""
        return self.graph.save_reports(final_state, label, save_path=save_path)
