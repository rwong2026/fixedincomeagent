import pytest

from fixedincomeagent.agents.schemas import (
    DirectionCall,
    ShapeCall,
    render_direction_call,
    render_shape_call,
)


def test_direction_call_valid():
    dc = DirectionCall(
        tenor="10Y",
        direction="up",
        magnitude_bucket="10-25bp",
        confidence=0.75,
        rationale="Hawkish Fed + sticky services inflation",
    )
    assert dc.tenor == "10Y"
    assert dc.direction == "up"
    assert dc.confidence == 0.75

def test_direction_call_rejects_invalid_tenor():
    with pytest.raises(ValueError):
        DirectionCall(
            tenor="15Y",  # not in allowed set
            direction="up",
            magnitude_bucket="<10bp",
            confidence=0.5,
            rationale="test",
        )

def test_direction_call_rejects_invalid_direction():
    with pytest.raises(ValueError):
        DirectionCall(
            tenor="10Y",
            direction="sideways",
            magnitude_bucket="<10bp",
            confidence=0.5,
            rationale="test",
        )

def test_shape_call_valid():
    sc = ShapeCall(
        spread="2s10s",
        shape="steepen",
        confidence=0.6,
        rationale="Front-end rally on rate-cut expectations",
    )
    assert sc.spread == "2s10s"
    assert sc.shape == "steepen"

def test_shape_call_rejects_invalid_spread():
    with pytest.raises(ValueError):
        ShapeCall(
            spread="3s7s",
            shape="steepen",
            confidence=0.5,
            rationale="test",
        )

def test_render_direction_call():
    dc = DirectionCall(
        tenor="2Y", direction="down", magnitude_bucket="25bp+",
        confidence=0.8, rationale="Rate cuts priced in",
    )
    rendered = render_direction_call(dc)
    assert "2Y" in rendered
    assert "down" in rendered
    assert "25bp+" in rendered

def test_render_shape_call():
    sc = ShapeCall(
        spread="5s30s", shape="flatten", confidence=0.65,
        rationale="Long end selling off",
    )
    rendered = render_shape_call(sc)
    assert "5s30s" in rendered
    assert "flatten" in rendered
