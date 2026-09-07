"""Guard the news analyst prompt against tool-signature drift (#1116).

The prompt used to advertise ``get_news(query, ...)`` while the tool takes a
``ticker``, tricking the LLM into hallucinating free-text query calls.
"""
import inspect

import pytest

import fixedincomeagent.agents.analysts.news_analyst as na
from fixedincomeagent.agents.utils.news_data_tools import get_news


@pytest.mark.unit
def test_get_news_takes_ticker_not_query():
    arg_names = set(get_news.args.keys())
    assert "ticker" in arg_names
    assert "query" not in arg_names


@pytest.mark.unit
def test_news_prompt_matches_get_news_signature():
    src = inspect.getsource(na)
    assert "get_news(ticker, start_date, end_date)" in src
    assert "get_news(query" not in src


@pytest.mark.unit
def test_news_prompt_decomposes_rate_action_probabilities():
    """The prompt must instruct the LLM to distinguish cut/hold/hike."""
    src = inspect.getsource(na)
    assert "rate hike" in src.lower() or "hike probability" in src.lower(), (
        "News analyst prompt must mention 'rate hike' to prevent conflating "
        "'no cut' with 'hold'."
    )
