"""Tests for ALFRED point-in-time vintage fetcher.

The three live-key tests are skipped without FRED_API_KEY; the mocked tests
run offline and are the real verification of behavior.
"""
import os
import unittest
from unittest import mock

import pytest

from fixedincomeagent.dataflows import alfred
from fixedincomeagent.dataflows.alfred import get_alfred_vintage, get_vintage_dates

_needs_key = pytest.mark.skipif(
    not os.getenv("FRED_API_KEY"), reason="FRED_API_KEY not set"
)


@_needs_key
def test_get_vintage_dates_cpi():
    """CPIAUCSL has many vintage dates; verify we get a non-empty list."""
    dates = get_vintage_dates("CPIAUCSL", limit=5)
    assert isinstance(dates, list)
    assert len(dates) > 0


@_needs_key
def test_get_alfred_vintage_returns_markdown():
    """Vintage fetch for a known series on a known date returns markdown."""
    result = get_alfred_vintage("CPIAUCSL", "2023-01-15", look_back_days=90)
    assert isinstance(result, str)
    assert "CPIAUCSL" in result or "CPI" in result


@_needs_key
def test_get_alfred_vintage_future_date_clamps():
    """A vintage date in the future should clamp to FRED's today, not error."""
    result = get_alfred_vintage("CPIAUCSL", "2099-01-01", look_back_days=30)
    assert isinstance(result, str)
    assert "error" not in result.lower() or "no observations" in result.lower()


_META = {
    "seriess": [
        {
            "title": "Consumer Price Index for All Urban Consumers",
            "units_short": "Index 1982-1984=100",
            "frequency": "Monthly",
        }
    ]
}
_OBS = {
    "observations": [
        {"date": "2022-11-01", "value": "298.1"},
        {"date": "2022-12-01", "value": "."},  # missing -> skipped
        {"date": "2023-01-01", "value": "299.2"},
    ]
}
_VDATES = {"vintage_dates": ["2023-01-01", "2023-01-08", "2023-01-15"]}


def _request_stub(meta=_META, obs=_OBS):
    """Build an alfred._request replacement that dispatches on endpoint path."""
    def _impl(path, params):
        if path == "series":
            return meta
        if path == "series/observations":
            return obs
        if path == "series/vintagedates":
            return _VDATES
        raise AssertionError(f"unexpected FRED path: {path}")
    return _impl


@pytest.mark.unit
class AlfredMockedTests(unittest.TestCase):
    def test_vintage_params_pinned_on_both_requests(self):
        calls = []

        def _spy(path, params):
            calls.append((path, dict(params)))
            return _request_stub()(path, params)

        with mock.patch.object(alfred, "_request", _spy):
            get_alfred_vintage("CPIAUCSL", "2023-01-15", look_back_days=90)

        realtime = {"realtime_start": "2023-01-15", "realtime_end": "2023-01-15"}
        for _path, params in calls:
            self.assertEqual(params["realtime_start"], realtime["realtime_start"])
            self.assertEqual(params["realtime_end"], realtime["realtime_end"])
        obs_params = dict(calls)[ "series/observations"]
        self.assertEqual(obs_params["observation_start"], "2022-10-17")
        self.assertEqual(obs_params["observation_end"], "2023-01-15")

    def test_future_vintage_date_clamps_to_fred_today(self):
        calls = []

        def _spy(path, params):
            calls.append(params)
            return _request_stub()(path, params)

        with mock.patch.object(alfred, "_request", _spy):
            get_alfred_vintage("CPIAUCSL", "2099-01-01", look_back_days=30)

        for params in calls:
            self.assertLessEqual(params["realtime_start"], alfred._fred_today())

    def test_markdown_header_summary_table_and_missing_skipped(self):
        with mock.patch.object(alfred, "_request", _request_stub()):
            out = get_alfred_vintage("CPIAUCSL", "2023-01-15", look_back_days=90)

        self.assertIn("## ALFRED Vintage:", out)
        self.assertIn("CPIAUCSL", out)
        self.assertIn("Vintage date (data as-known): 2023-01-15", out)
        self.assertIn("**Latest:** 299.2 (2023-01-01)", out)
        self.assertIn("| Date | Value |", out)
        self.assertIn("| 2022-11-01 | 298.1 |", out)
        # Missing value "." skipped: no row for 2022-12-01.
        self.assertNotIn("2022-12-01", out)

    def test_no_observations_handled(self):
        with mock.patch.object(
            alfred, "_request", _request_stub(obs={"observations": []})
        ):
            out = get_alfred_vintage("CPIAUCSL", "2023-01-15", look_back_days=90)
        self.assertIn("No observations", out)
        self.assertIn("CPIAUCSL", out)

    def test_series_not_found_at_vintage(self):
        with mock.patch.object(
            alfred, "_request", _request_stub(meta={"seriess": []})
        ):
            out = get_alfred_vintage("NOPE", "2023-01-15")
        self.assertIn("not found at vintage", out)

    def test_get_vintage_dates_limit_slices_most_recent(self):
        with mock.patch.object(alfred, "_request", _request_stub()):
            self.assertEqual(get_vintage_dates("CPIAUCSL"), ["2023-01-01", "2023-01-08", "2023-01-15"])
            self.assertEqual(get_vintage_dates("CPIAUCSL", limit=2), ["2023-01-08", "2023-01-15"])

    def test_network_error_returns_clean_message(self):
        import requests

        with mock.patch.object(
            alfred, "_request", side_effect=requests.exceptions.ConnectionError("Failed to resolve")
        ):
            out = get_alfred_vintage("CPIAUCSL", "2023-01-15")
        self.assertIn("unavailable due to network error", out)
        self.assertIn("CPIAUCSL", out)

    def test_get_vintage_dates_network_error_returns_empty_list(self):
        import requests

        with mock.patch.object(
            alfred, "_request", side_effect=requests.exceptions.ConnectionError("Failed to resolve")
        ):
            dates = get_vintage_dates("CPIAUCSL")
        self.assertEqual(dates, [])
