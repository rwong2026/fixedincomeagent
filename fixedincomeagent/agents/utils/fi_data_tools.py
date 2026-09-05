"""LangChain @tool wrappers for the Phase 1 fixed-income data modules.

Every wrapper routes through ``route_to_vendor`` so vendor selection and
error handling stay in ``dataflows.interface``; the docstrings below are
what the LLM sees when deciding which tool to call.
"""
from typing import Annotated

from langchain_core.tools import tool

from fixedincomeagent.dataflows.interface import route_to_vendor


@tool
def get_treasury_par_yields(
    curr_date: Annotated[str, "As-of date in yyyy-mm-dd format"],
    look_back_days: Annotated[
        int, "Trailing window length in days; omit for a 90-day window"
    ] = 90,
) -> str:
    """
    Retrieve the daily U.S. Treasury par yield curve (all tenors from 1-month
    to 30-year) from the U.S. Treasury. Returns a markdown report of recent
    daily curves across the window — the raw input for curve-level, slope,
    and curvature analysis. Rows after curr_date are excluded, so historical
    runs never see future yields.

    Args:
        curr_date (str): As-of date in yyyy-mm-dd format
        look_back_days (int): Trailing window length; omit for a 90-day window

    Returns:
        str: A formatted markdown report of the par yield curve
    """
    return route_to_vendor("get_treasury_par_yields", curr_date, look_back_days)


@tool
def get_auction_results(
    curr_date: Annotated[str, "As-of date in yyyy-mm-dd format"],
    look_back_days: Annotated[
        int, "Trailing window length in days; omit for a 90-day window"
    ] = 90,
) -> str:
    """
    Retrieve recent U.S. Treasury auction results (notes and bonds): security
    type and term, auction date, high yield, bid-to-cover ratio, and tail.
    Use for supply/demand pressure on the rates curve.

    Args:
        curr_date (str): As-of date in yyyy-mm-dd format
        look_back_days (int): Trailing window length; omit for a 90-day window

    Returns:
        str: A formatted markdown report of recent auction results
    """
    return route_to_vendor("get_auction_results", curr_date, look_back_days)


@tool
def get_fomc_calendar(
    curr_date: Annotated[str, "As-of date in yyyy-mm-dd format"],
) -> str:
    """
    Retrieve the FOMC meeting calendar around the as-of date: recent and
    upcoming meeting dates, rate decisions, and statement links. Use to
    anchor policy expectations and event risk for rates analysis.

    Args:
        curr_date (str): As-of date in yyyy-mm-dd format

    Returns:
        str: A formatted markdown report of the FOMC calendar
    """
    return route_to_vendor("get_fomc_calendar", curr_date)


@tool
def get_fed_speeches(
    curr_date: Annotated[str, "As-of date in yyyy-mm-dd format"],
    look_back_days: Annotated[
        int, "Trailing window length in days; omit for a 14-day window"
    ] = 14,
) -> str:
    """
    Retrieve recent Federal Reserve speeches and testimony (titles, speakers,
    dates, links) from the Fed's official feeds. Use to gauge the policy
    tone of FOMC members heading into a meeting.

    Args:
        curr_date (str): As-of date in yyyy-mm-dd format
        look_back_days (int): Trailing window length; omit for a 14-day window

    Returns:
        str: A formatted markdown report of recent Fed communications
    """
    return route_to_vendor("get_fed_speeches", curr_date, look_back_days)


@tool
def get_fred_series(
    indicator: Annotated[
        str,
        "FRED series: a friendly alias such as 'cpi', 'core_pce', "
        "'unemployment', 'fed_funds_rate', '10y_treasury', 'yield_curve', "
        "'real_gdp', 'vix', or a raw FRED series ID such as 'CPIAUCSL'.",
    ],
    curr_date: Annotated[str, "As-of date in yyyy-mm-dd format; the end of the window"],
    look_back_days: Annotated[
        int | None, "Trailing window length in days; omit for a 1-year window"
    ] = None,
) -> str:
    """
    Retrieve any FRED (Federal Reserve Economic Data) series: policy rates,
    Treasury yields, inflation, labor, and growth. Returns the series title,
    units, frequency, the latest value, the change over the window, and a
    recent observation table.

    Args:
        indicator (str): Friendly alias or raw FRED series ID
        curr_date (str): As-of date in yyyy-mm-dd format
        look_back_days (int): Trailing window length; omit for a 1-year window

    Returns:
        str: A formatted markdown report of the FRED series
    """
    return route_to_vendor("get_fred_series", indicator, curr_date, look_back_days)


@tool
def get_alfred_vintage(
    series_id: Annotated[str, "FRED series ID, e.g. 'CPIAUCSL', 'PAYEMS', 'GDP'"],
    vintage_date: Annotated[
        str, "Vintage date in yyyy-mm-dd format: the data as known on that day"
    ],
    look_back_days: Annotated[
        int | None, "Trailing window length in days; omit for the full window"
    ] = None,
) -> str:
    """
    Retrieve a FRED series as it was known on a specific vintage date
    (ALFRED), i.e. before any later revisions. Use for point-in-time
    analysis: what policymakers actually saw when they decided.

    Args:
        series_id (str): FRED series ID (e.g. 'CPIAUCSL', 'PAYEMS', 'GDP')
        vintage_date (str): Vintage date in yyyy-mm-dd format
        look_back_days (int): Trailing window length; omit for the full window

    Returns:
        str: A formatted markdown report of the vintage series
    """
    return route_to_vendor("get_alfred_vintage", series_id, vintage_date, look_back_days)


@tool
def get_inflation_breakevens(
    curr_date: Annotated[str, "As-of date in yyyy-mm-dd format"],
    look_back_days: Annotated[
        int, "Trailing window length in days; omit for a 1-year window"
    ] = 365,
) -> str:
    """
    Retrieve TIPS inflation breakeven rates (5-year, 10-year, and 5y5y
    forward) from FRED: market-implied inflation expectations derived from
    nominal minus real Treasury yields.

    Args:
        curr_date (str): As-of date in yyyy-mm-dd format
        look_back_days (int): Trailing window length; omit for a 1-year window

    Returns:
        str: A formatted markdown report of inflation breakevens
    """
    return route_to_vendor("get_inflation_breakevens", curr_date, look_back_days)


@tool
def get_inflation_nowcast(
    curr_date: Annotated[str, "As-of date in yyyy-mm-dd format"],
) -> str:
    """
    Retrieve the Cleveland Fed inflation nowcast: model-based estimates of
    current-quarter CPI and PCE inflation before official releases. Use as
    a high-frequency read on where inflation prints are heading.

    Args:
        curr_date (str): As-of date in yyyy-mm-dd format

    Returns:
        str: A formatted markdown report of the inflation nowcast
    """
    return route_to_vendor("get_inflation_nowcast", curr_date)


@tool
def get_shelter_rents(
    curr_date: Annotated[str, "As-of date in yyyy-mm-dd format"],
) -> str:
    """
    Retrieve market-based shelter rent indices (Zillow observed rents and
    Apartment List asking rents): leading indicators for the shelter
    component of CPI, which lags market rents by roughly a year.

    Args:
        curr_date (str): As-of date in yyyy-mm-dd format

    Returns:
        str: A formatted markdown report of shelter rent inflation
    """
    return route_to_vendor("get_shelter_rents", curr_date)


@tool
def get_used_vehicle_index(
    curr_date: Annotated[str, "As-of date in yyyy-mm-dd format"],
) -> str:
    """
    Retrieve the Manheim used vehicle price index: a leading indicator for
    the used cars and trucks component of CPI goods inflation.

    Args:
        curr_date (str): As-of date in yyyy-mm-dd format

    Returns:
        str: A formatted markdown report of the used vehicle index
    """
    return route_to_vendor("get_used_vehicle_index", curr_date)


@tool
def get_ism_prices_paid(
    curr_date: Annotated[str, "As-of date in yyyy-mm-dd format"],
) -> str:
    """
    Retrieve the ISM manufacturing Prices Paid index: a survey-based leading
    indicator of pipeline inflation pressure on goods producers.

    Args:
        curr_date (str): As-of date in yyyy-mm-dd format

    Returns:
        str: A formatted markdown report of ISM prices paid
    """
    return route_to_vendor("get_ism_prices_paid", curr_date)


@tool
def get_supply_chain_pressure(
    curr_date: Annotated[str, "As-of date in yyyy-mm-dd format"],
) -> str:
    """
    Retrieve the New York Fed Global Supply Chain Pressure Index (GSCPI):
    a composite of transportation costs and supply-side frictions, a leading
    indicator for goods inflation.

    Args:
        curr_date (str): As-of date in yyyy-mm-dd format

    Returns:
        str: A formatted markdown report of supply chain pressure
    """
    return route_to_vendor("get_supply_chain_pressure", curr_date)


@tool
def get_consumer_inflation_expectations(
    curr_date: Annotated[str, "As-of date in yyyy-mm-dd format"],
) -> str:
    """
    Retrieve the New York Fed Survey of Consumer Expectations inflation
    expectations (1-year and 3-year ahead medians): household inflation
    sentiment the Fed watches for de-anchoring risk.

    Args:
        curr_date (str): As-of date in yyyy-mm-dd format

    Returns:
        str: A formatted markdown report of consumer inflation expectations
    """
    return route_to_vendor("get_consumer_inflation_expectations", curr_date)


@tool
def get_cot_data(
    curr_date: Annotated[str, "As-of date in yyyy-mm-dd format"],
    contract: Annotated[
        str,
        "Treasury futures contract: 'UST_2Y', 'UST_5Y', 'UST_10Y', 'UST_30Y', "
        "or 'UST_ULTRA'; omit for 10-Year Note futures",
    ] = "UST_10Y",
) -> str:
    """
    Retrieve CFTC Commitments of Traders positioning for U.S. Treasury
    futures: net long/short by dealer, asset manager, and leveraged money
    categories. Use for positioning and sentiment on the rates curve.

    Args:
        curr_date (str): As-of date in yyyy-mm-dd format
        contract (str): Treasury futures contract code; omit for UST_10Y

    Returns:
        str: A formatted markdown report of COT positioning
    """
    return route_to_vendor("get_cot_data", curr_date, contract)
