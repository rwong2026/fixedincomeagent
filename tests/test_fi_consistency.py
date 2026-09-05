"""Fixed-Income Risk Consistency Check (Task 5.2).

Pure-logic validator between the FI trader and the portfolio manager:
- ``parse_trader_decision`` re-parses the trader's rendered markdown back
  into DirectionCall/ShapeCall objects (tolerant: unknown blocks ignored).
- ``check_consistency`` flags direction/shape contradictions without
  overriding them.
- ``fi_consistency_check_node`` annotates the affected shape calls'
  rationales and overwrites ``trader_investment_plan`` in state.
"""
from __future__ import annotations

from fixedincomeagent.agents.risk_mgmt.fi_consistency_checker import (
    check_consistency,
    fi_consistency_check_node,
    parse_trader_decision,
)
from fixedincomeagent.agents.schemas import (
    DirectionCall,
    ShapeCall,
    TraderDecision,
    render_direction_call,
    render_shape_call,
    render_trader_decision,
)


def _dc(tenor, direction, bucket, confidence=0.7, rationale="r"):
    return DirectionCall(
        tenor=tenor,
        direction=direction,
        magnitude_bucket=bucket,
        confidence=confidence,
        rationale=rationale,
    )


def _sc(spread, shape, confidence=0.6, rationale="r"):
    return ShapeCall(
        spread=spread, shape=shape, confidence=confidence, rationale=rationale
    )


# ---------------------------------------------------------------------------
# Parser round-trips
# ---------------------------------------------------------------------------


def test_parse_round_trips_render_direction_call():
    dc = _dc("2Y", "up", "10-25bp", confidence=0.75, rationale="front end sells off")
    parsed_dirs, parsed_shapes = parse_trader_decision(render_direction_call(dc))
    assert parsed_shapes == []
    assert len(parsed_dirs) == 1
    assert parsed_dirs[0] == dc


def test_parse_round_trips_render_shape_call():
    sc = _sc("2s10s", "steepen", confidence=0.6, rationale="long end leads")
    parsed_dirs, parsed_shapes = parse_trader_decision(render_shape_call(sc))
    assert parsed_dirs == []
    assert len(parsed_shapes) == 1
    assert parsed_shapes[0] == sc


def test_parse_round_trips_full_trader_decision():
    decision = TraderDecision(
        direction_calls=[
            _dc("2Y", "up", "25bp+", 0.8, "two year"),
            _dc("5Y", "neutral", "<10bp", 0.5, "five year"),
            _dc("10Y", "down", "10-25bp", 0.65, "ten year"),
            _dc("30Y", "up", "<10bp", 0.55, "thirty year"),
        ],
        shape_calls=[
            _sc("2s10s", "flatten", 0.6, "twos tens"),
            _sc("5s30s", "unchanged", 0.5, "fives thirties"),
            _sc("2s5s10s_fly", "steepen", 0.7, "fly"),
        ],
    )
    parsed_dirs, parsed_shapes = parse_trader_decision(
        render_trader_decision(decision)
    )
    assert parsed_dirs == decision.direction_calls
    assert parsed_shapes == decision.shape_calls


def test_parse_ignores_unrelated_markdown():
    parsed_dirs, parsed_shapes = parse_trader_decision(
        "## Some equity plan\n\n**AAPL**: buy 100 shares\n\nFree text here."
    )
    assert parsed_dirs == []
    assert parsed_shapes == []


# ---------------------------------------------------------------------------
# 2s10s rule
# ---------------------------------------------------------------------------


def test_consistent_steepener_no_warning():
    dirs = [_dc("10Y", "up", "25bp+"), _dc("2Y", "up", "<10bp")]
    shapes = [_sc("2s10s", "steepen")]
    assert check_consistency(dirs, shapes) == []


def test_consistent_flattener_no_warning():
    dirs = [_dc("2Y", "up", "25bp+"), _dc("10Y", "up", "<10bp")]
    shapes = [_sc("2s10s", "flatten")]
    assert check_consistency(dirs, shapes) == []


def test_front_end_leads_but_steepen_call_flagged():
    dirs = [_dc("2Y", "up", "25bp+"), _dc("10Y", "up", "<10bp")]
    shapes = [_sc("2s10s", "steepen")]
    warnings = check_consistency(dirs, shapes)
    assert len(warnings) == 1
    assert warnings[0].spread == "2s10s"
    assert "flatten" in warnings[0].message


def test_long_end_leads_but_flatten_call_flagged():
    dirs = [_dc("10Y", "up", "25bp+"), _dc("2Y", "up", "10-25bp")]
    shapes = [_sc("2s10s", "flatten")]
    warnings = check_consistency(dirs, shapes)
    assert len(warnings) == 1
    assert warnings[0].spread == "2s10s"
    assert "steepen" in warnings[0].message


def test_down_moves_use_signed_buckets():
    # 2Y down 25bp+ (-3) vs 10Y down <10bp (-1): 10Y falls less -> steepening.
    dirs = [_dc("2Y", "down", "25bp+"), _dc("10Y", "down", "<10bp")]
    warnings = check_consistency(dirs, [_sc("2s10s", "flatten")])
    assert len(warnings) == 1
    assert "steepen" in warnings[0].message


def test_neutral_tenor_skips_2s10s_check():
    dirs = [_dc("2Y", "neutral", "<10bp"), _dc("10Y", "up", "25bp+")]
    shapes = [_sc("2s10s", "flatten")]
    assert check_consistency(dirs, shapes) == []


def test_equal_buckets_no_warning():
    dirs = [_dc("2Y", "up", "10-25bp"), _dc("10Y", "up", "10-25bp")]
    shapes = [_sc("2s10s", "steepen")]
    assert check_consistency(dirs, shapes) == []


# ---------------------------------------------------------------------------
# 2s5s10s butterfly rule
# ---------------------------------------------------------------------------


def test_belly_outperforms_and_fly_steepens_no_warning():
    dirs = [
        _dc("2Y", "up", "<10bp"),
        _dc("5Y", "up", "25bp+"),
        _dc("30Y", "up", "<10bp"),
    ]
    assert check_consistency(dirs, [_sc("2s5s10s_fly", "steepen")]) == []


def test_belly_outperforms_but_fly_flatten_flagged():
    dirs = [
        _dc("2Y", "up", "<10bp"),
        _dc("5Y", "up", "25bp+"),
        _dc("30Y", "up", "<10bp"),
    ]
    warnings = check_consistency(dirs, [_sc("2s5s10s_fly", "flatten")])
    assert len(warnings) == 1
    assert warnings[0].spread == "2s5s10s_fly"


def test_belly_underperforms_but_fly_steepen_flagged():
    dirs = [
        _dc("2Y", "up", "25bp+"),
        _dc("5Y", "up", "<10bp"),
        _dc("30Y", "up", "25bp+"),
    ]
    warnings = check_consistency(dirs, [_sc("2s5s10s_fly", "steepen")])
    assert len(warnings) == 1
    assert warnings[0].spread == "2s5s10s_fly"


def test_fly_check_skipped_when_any_leg_neutral():
    dirs = [
        _dc("2Y", "neutral", "<10bp"),
        _dc("5Y", "up", "25bp+"),
        _dc("30Y", "up", "<10bp"),
    ]
    assert check_consistency(dirs, [_sc("2s5s10s_fly", "flatten")]) == []


def test_fly_balanced_belly_no_warning():
    dirs = [
        _dc("2Y", "up", "10-25bp"),
        _dc("5Y", "up", "10-25bp"),
        _dc("30Y", "up", "10-25bp"),
    ]
    assert check_consistency(dirs, [_sc("2s5s10s_fly", "steepen")]) == []


def test_unknown_spread_ignored():
    dirs = [_dc("2Y", "up", "25bp+"), _dc("10Y", "up", "<10bp")]
    shapes = [_sc("5s30s", "steepen")]
    assert check_consistency(dirs, shapes) == []


def test_missing_calls_no_crash():
    assert check_consistency([], []) == []
    assert check_consistency([_dc("2Y", "up", "25bp+")], []) == []


# ---------------------------------------------------------------------------
# Graph node
# ---------------------------------------------------------------------------


def _state_with(decision: TraderDecision) -> dict:
    return {"trader_investment_plan": render_trader_decision(decision)}


def test_node_annotates_affected_call_and_overwrites_plan():
    decision = TraderDecision(
        direction_calls=[_dc("2Y", "up", "25bp+"), _dc("10Y", "up", "<10bp")],
        shape_calls=[_sc("2s10s", "steepen", rationale="curve call")],
    )
    out = fi_consistency_check_node(_state_with(decision))
    plan = out["trader_investment_plan"]
    assert "CONSISTENCY WARNING" in plan
    assert "curve call" in plan
    # Output re-parses cleanly: only the rationale changed.
    dirs, shapes = parse_trader_decision(plan)
    assert dirs == decision.direction_calls
    assert len(shapes) == 1
    assert shapes[0].spread == "2s10s"
    assert "CONSISTENCY WARNING" in shapes[0].rationale


def test_node_without_warnings_returns_plan_unchanged():
    decision = TraderDecision(
        direction_calls=[_dc("2Y", "up", "25bp+"), _dc("10Y", "up", "<10bp")],
        shape_calls=[_sc("2s10s", "flatten")],
    )
    state = _state_with(decision)
    out = fi_consistency_check_node(state)
    assert out["trader_investment_plan"] == state["trader_investment_plan"]


def test_node_passes_through_non_fi_plan():
    state = {"trader_investment_plan": "## Equity plan\n\nBuy AAPL."}
    out = fi_consistency_check_node(state)
    assert out["trader_investment_plan"] == state["trader_investment_plan"]
