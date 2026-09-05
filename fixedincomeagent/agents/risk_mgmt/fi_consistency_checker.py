"""Fixed-Income Risk Consistency Check: pure-logic validator (no LLM).

Sits between the FI trader and the portfolio manager. The trader's output in
state is rendered markdown under ``trader_investment_plan``, so the checker
re-parses it back into DirectionCall/ShapeCall objects with a tolerant
regex-based parser, runs the consistency rules, and — when a rule fires —
appends a warning to the affected shape call's rationale and overwrites
``trader_investment_plan`` with the annotated re-render. The original calls
are never overridden; downstream sees the same plan plus the warnings.

Rules (flag only, never override):
- 2s10s: with both 2Y and 10Y directional, the tenor with the larger signed
  expected move sets the curve direction — 2Y leading implies flattening,
  10Y leading implies steepening. A directly contradictory 2s10s shape call
  is flagged ("unchanged" is not flagged).
- 2s5s10s_fly: with 2Y, 5Y, and 30Y all directional, if the 5Y move exceeds
  the average of the 2Y and 30Y moves (belly outperforming the wings) the
  fly should steepen; if it falls short the fly should flatten. A directly
  contradictory fly call is flagged.

Explicitly NOT built: DV01 / portfolio-level risk sizing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from fixedincomeagent.agents.schemas import (
    DirectionCall,
    ShapeCall,
    TraderDecision,
    render_trader_decision,
)

_WARNING_PREFIX = "CONSISTENCY WARNING"

# Rationale runs until the next rendered call block, the next section
# header, or end of text.
_BLOCK_END = r"(?=\n\n\*\*|\n\n##|\Z)"

_DIRECTION_RE = re.compile(
    r"\*\*(?P<tenor>2Y|5Y|10Y|30Y)\*\*:\s*"
    r"(?P<direction>up|down|neutral)\s*"
    r"\((?P<bucket><10bp|10-25bp|25bp\+)\)\s*"
    r"\[confidence:\s*(?P<confidence>\d+)%\]\s*"
    r"\nRationale:\s*(?P<rationale>.*?)" + _BLOCK_END,
    re.DOTALL,
)

_SHAPE_RE = re.compile(
    r"\*\*(?P<spread>2s10s|5s30s|2s5s10s_fly)\*\*:\s*"
    r"(?P<shape>steepen|flatten|unchanged)\s*"
    r"\[confidence:\s*(?P<confidence>\d+)%\]\s*"
    r"\nRationale:\s*(?P<rationale>.*?)" + _BLOCK_END,
    re.DOTALL,
)

_BUCKET_ORDER = {"<10bp": 1, "10-25bp": 2, "25bp+": 3}


@dataclass(frozen=True)
class ConsistencyWarning:
    """A direction/shape contradiction attached to a shape call."""

    spread: str
    message: str


def parse_trader_decision(
    markdown: str,
) -> tuple[list[DirectionCall], list[ShapeCall]]:
    """Re-parse rendered trader markdown into DirectionCall/ShapeCall lists.

    Tolerant: blocks that do not match the render format are ignored, so
    non-FI plans (e.g. equity free text) parse to empty lists.
    """
    direction_calls = [
        DirectionCall(
            tenor=m.group("tenor"),
            direction=m.group("direction"),
            magnitude_bucket=m.group("bucket"),
            confidence=int(m.group("confidence")) / 100,
            rationale=m.group("rationale").strip(),
        )
        for m in _DIRECTION_RE.finditer(markdown)
    ]
    shape_calls = [
        ShapeCall(
            spread=m.group("spread"),
            shape=m.group("shape"),
            confidence=int(m.group("confidence")) / 100,
            rationale=m.group("rationale").strip(),
        )
        for m in _SHAPE_RE.finditer(markdown)
    ]
    return direction_calls, shape_calls


def _signed_move(call: DirectionCall) -> int:
    """Signed magnitude ordinal: up positive, down negative, neutral zero."""
    if call.direction == "neutral":
        return 0
    magnitude = _BUCKET_ORDER[call.magnitude_bucket]
    return magnitude if call.direction == "up" else -magnitude


def _is_directional(call: DirectionCall) -> bool:
    return call.direction != "neutral"


def check_consistency(
    direction_calls: list[DirectionCall],
    shape_calls: list[ShapeCall],
) -> list[ConsistencyWarning]:
    """Flag direction/shape contradictions. Never overrides a call.

    A rule only fires when every tenor it needs is present and directional;
    equal signed moves impose no constraint; unrecognized spreads are
    ignored.
    """
    directions = {call.tenor: call for call in direction_calls}
    shapes = {call.spread: call for call in shape_calls}
    warnings: list[ConsistencyWarning] = []

    c2, c10 = directions.get("2Y"), directions.get("10Y")
    spread_2s10s = shapes.get("2s10s")
    if (
        c2 is not None and c10 is not None and spread_2s10s is not None
        and _is_directional(c2) and _is_directional(c10)
    ):
        m2, m10 = _signed_move(c2), _signed_move(c10)
        if m2 > m10 and spread_2s10s.shape == "steepen":
            warnings.append(ConsistencyWarning(
                spread="2s10s",
                message=(
                    f"2Y {c2.direction} ({c2.magnitude_bucket}) implies a "
                    f"larger move than 10Y {c10.direction} "
                    f"({c10.magnitude_bucket}), which flattens 2s10s — but "
                    "the 2s10s shape call is 'steepen'."
                ),
            ))
        elif m10 > m2 and spread_2s10s.shape == "flatten":
            warnings.append(ConsistencyWarning(
                spread="2s10s",
                message=(
                    f"10Y {c10.direction} ({c10.magnitude_bucket}) implies a "
                    f"larger move than 2Y {c2.direction} "
                    f"({c2.magnitude_bucket}), which steepens 2s10s — but "
                    "the 2s10s shape call is 'flatten'."
                ),
            ))

    c5, c30 = directions.get("5Y"), directions.get("30Y")
    fly = shapes.get("2s5s10s_fly")
    if (
        c2 is not None and c5 is not None and c30 is not None
        and fly is not None
        and _is_directional(c2) and _is_directional(c5) and _is_directional(c30)
    ):
        belly = _signed_move(c5)
        wings_avg = (_signed_move(c2) + _signed_move(c30)) / 2
        if belly > wings_avg and fly.shape == "flatten":
            warnings.append(ConsistencyWarning(
                spread="2s5s10s_fly",
                message=(
                    f"5Y {c5.direction} ({c5.magnitude_bucket}) exceeds the "
                    "average of the 2Y and 30Y moves (belly outperforming "
                    "the wings), which steepens the 2s5s10s fly — but the "
                    "fly shape call is 'flatten'."
                ),
            ))
        elif belly < wings_avg and fly.shape == "steepen":
            warnings.append(ConsistencyWarning(
                spread="2s5s10s_fly",
                message=(
                    f"5Y {c5.direction} ({c5.magnitude_bucket}) falls short "
                    "of the average of the 2Y and 30Y moves (belly "
                    "underperforming the wings), which flattens the "
                    "2s5s10s fly — but the fly shape call is 'steepen'."
                ),
            ))

    return warnings


def _annotate(
    shape_calls: list[ShapeCall], warnings: list[ConsistencyWarning]
) -> list[ShapeCall]:
    by_spread: dict[str, list[str]] = {}
    for warning in warnings:
        by_spread.setdefault(warning.spread, []).append(warning.message)
    return [
        call.model_copy(update={
            "rationale": (
                call.rationale
                + "".join(
                    f"\n\n{_WARNING_PREFIX}: {message}"
                    for message in by_spread[call.spread]
                )
            )
        })
        if call.spread in by_spread else call
        for call in shape_calls
    ]


def fi_consistency_check_node(state) -> dict:
    """Graph node: validate ``trader_investment_plan`` and flag conflicts.

    Parses the rendered plan, runs the consistency rules, and overwrites
    ``trader_investment_plan`` with the annotated re-render when any rule
    fires. Plans that parse to no FI calls (e.g. equity free text) and
    plans without warnings pass through unchanged.
    """
    plan = state.get("trader_investment_plan") or ""
    direction_calls, shape_calls = parse_trader_decision(plan)
    warnings = check_consistency(direction_calls, shape_calls)
    if not warnings:
        return {"trader_investment_plan": plan}
    annotated = TraderDecision(
        direction_calls=direction_calls,
        shape_calls=_annotate(shape_calls, warnings),
    )
    return {"trader_investment_plan": render_trader_decision(annotated)}
