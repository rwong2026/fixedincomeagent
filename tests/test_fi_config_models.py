import pytest
from pydantic import ValidationError

from fixedincomeagent.default_config import DEFAULT_CONFIG
from fixedincomeagent.fi_config_models import CentralBank, Curve


def test_config_curves_parse_into_curve_model():
    curves = {k: Curve(**v) for k, v in DEFAULT_CONFIG["fi_curves"].items()}
    usd = curves["USD"]
    assert usd.currency == "USD"
    assert usd.curve_type == "UST"
    assert usd.tenors == ["2Y", "5Y", "10Y", "30Y"]
    assert usd.tenor_series["10Y"] == "DGS10"


def test_config_central_banks_parse_into_model():
    banks = {k: CentralBank(**v) for k, v in DEFAULT_CONFIG["fi_central_banks"].items()}
    fed = banks["USD"]
    assert fed.currency == "USD"
    assert fed.name == "Fed"
    assert fed.policy_rate_series == "DFEDTARU"
    assert fed.funding_rate_series == "SOFR"
    assert fed.meeting_calendar_source == "fomc_calendar"
    assert fed.speech_source == "fed_speeches"


def test_curve_requires_all_fields():
    with pytest.raises(ValidationError):
        Curve(currency="USD", curve_type="UST", tenors=["2Y"])


def test_central_bank_requires_all_fields():
    with pytest.raises(ValidationError):
        CentralBank(currency="USD", name="Fed")
