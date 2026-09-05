"""Task 1.12: all Phase 1 fixed-income data tools are registered in the
interface (TOOLS_CATEGORIES / VENDOR_METHODS) and re-exported from
agent_utils as callable LangChain @tool wrappers that route to the right
dataflows implementation.

Offline: importing agent_utils and calling the wrappers (with the vendor
implementation mocked) must not trigger any network access.
"""
import copy
from unittest import mock

import pytest

import fixedincomeagent.dataflows.config as config_module
import fixedincomeagent.default_config as default_config
from fixedincomeagent.dataflows import interface
from fixedincomeagent.agents.utils.agent_utils import (
    get_alfred_vintage,
    get_auction_results,
    get_consumer_inflation_expectations,
    get_cot_data,
    get_fed_speeches,
    get_fomc_calendar,
    get_fred_series,
    get_inflation_breakevens,
    get_inflation_nowcast,
    get_ism_prices_paid,
    get_shelter_rents,
    get_supply_chain_pressure,
    get_treasury_par_yields,
    get_used_vehicle_index,
)

ALL_TOOLS = [
    get_inflation_breakevens,
    get_inflation_nowcast,
    get_shelter_rents,
    get_supply_chain_pressure,
    get_consumer_inflation_expectations,
    get_used_vehicle_index,
    get_ism_prices_paid,
    get_fred_series,
    get_alfred_vintage,
    get_fomc_calendar,
    get_fed_speeches,
    get_treasury_par_yields,
    get_auction_results,
    get_cot_data,
]

# tool name -> (expected category, args the wrapper is called with)
REGISTRATION = {
    "get_treasury_par_yields": ("rates_data", ("2026-09-05",)),
    "get_auction_results": ("rates_data", ("2026-09-05",)),
    "get_fomc_calendar": ("rates_data", ("2026-09-05",)),
    "get_fed_speeches": ("rates_data", ("2026-09-05",)),
    "get_fred_series": ("rates_data", ("10y_treasury", "2026-09-05")),
    "get_alfred_vintage": ("rates_data", ("CPIAUCSL", "2026-01-15")),
    "get_inflation_breakevens": ("inflation_data", ("2026-09-05",)),
    "get_inflation_nowcast": ("inflation_data", ("2026-09-05",)),
    "get_shelter_rents": ("inflation_data", ("2026-09-05",)),
    "get_used_vehicle_index": ("inflation_data", ("2026-09-05",)),
    "get_ism_prices_paid": ("inflation_data", ("2026-09-05",)),
    "get_supply_chain_pressure": ("inflation_data", ("2026-09-05",)),
    "get_consumer_inflation_expectations": ("inflation_data", ("2026-09-05",)),
    "get_cot_data": ("positioning_data", ("2026-09-05",)),
}


@pytest.fixture(autouse=True)
def _reset_config():
    config_module._config = copy.deepcopy(default_config.DEFAULT_CONFIG)
    yield
    config_module._config = copy.deepcopy(default_config.DEFAULT_CONFIG)


def test_tools_are_callable():
    """All new FI data tools should be importable and invocable.

    LangChain StructuredTools are not Python-callable (``callable()`` is
    False); the real contract for agent binding is ``invoke``/``func``.
    """
    for t in ALL_TOOLS:
        assert hasattr(t, "invoke") and hasattr(t, "func"), f"{t!r} not invocable"


def test_tools_have_descriptions():
    """Docstrings are what the LLM sees — every tool must have one."""
    for t in ALL_TOOLS:
        assert t.description, f"{t.name} has no description"


@pytest.mark.parametrize("method", sorted(REGISTRATION))
def test_method_registered_in_interface(method):
    category, _ = REGISTRATION[method]
    assert interface.get_category_for_method(method) == category
    assert method in interface.VENDOR_METHODS
    assert interface.VENDOR_METHODS[method], f"{method} has no vendor"


@pytest.mark.parametrize("method", sorted(REGISTRATION))
def test_wrapper_routes_to_dataflows_impl(method):
    """Each @tool wrapper must invoke its registered dataflows function."""
    category, args = REGISTRATION[method]
    tool = next(t for t in ALL_TOOLS if t.name == method)
    impl = mock.Mock(return_value="REPORT")
    with mock.patch.dict(interface.VENDOR_METHODS, {method: {"stub": impl}}):
        out = tool.func(*args)
    assert out == "REPORT"
    impl.assert_called_once()
    assert impl.call_args.args[: len(args)] == args


def test_categories_exist_with_descriptions():
    for category in ("rates_data", "inflation_data", "positioning_data"):
        info = interface.TOOLS_CATEGORIES[category]
        assert info["description"]
        assert info["tools"]
