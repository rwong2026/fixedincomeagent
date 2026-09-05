"""Inflation breakevens fetcher: config-driven series set, consolidated markdown
report, premia caveat, missing-data handling, and lookahead-safe vintage pinning.

All API access is mocked at ``fred._request``, so these run offline with no
FRED_API_KEY.
"""
import copy
import unittest
from unittest import mock

import pytest

import fixedincomeagent.dataflows.config as config_module
import fixedincomeagent.default_config as default_config
from fixedincomeagent.dataflows import fred, inflation_breakevens

_OBS = {
    "T5YIE": {
        "observations": [
            {"date": "2025-09-02", "value": "2.40"},
            {"date": "2025-09-03", "value": "."},   # missing -> skipped
            {"date": "2025-09-04", "value": "2.45"},
        ]
    },
    "T10YIE": {
        "observations": [
            {"date": "2025-09-02", "value": "2.30"},
            {"date": "2025-09-04", "value": "2.35"},
        ]
    },
    "T5YIFR": {
        "observations": [
            {"date": "2025-09-02", "value": "2.20"},
            {"date": "2025-09-04", "value": "2.25"},
        ]
    },
}


def _request_stub(obs_by_series=_OBS, captured=None):
    """Build a fred._request replacement dispatching on series_id."""
    def _impl(path, params):
        if captured is not None:
            captured.setdefault(params["series_id"], []).append((path, params))
        if path != "series/observations":
            raise AssertionError(f"unexpected FRED path: {path}")
        return obs_by_series[params["series_id"]]
    return _impl


@pytest.mark.unit
class BreakevensFetchTests(unittest.TestCase):
    def setUp(self):
        config_module._config = copy.deepcopy(default_config.DEFAULT_CONFIG)

    def tearDown(self):
        config_module._config = copy.deepcopy(default_config.DEFAULT_CONFIG)

    def test_fetches_all_configured_series(self):
        captured = {}
        with mock.patch.object(fred, "_request", side_effect=_request_stub(captured=captured)):
            inflation_breakevens.get_inflation_breakevens("2025-09-30")
        self.assertEqual(set(captured), {"T5YIE", "T10YIE", "T5YIFR"})

    def test_series_come_from_config_not_hardcoded(self):
        captured = {}
        with mock.patch.dict(
            config_module._config,
            {"fi_breakeven_series": {"2Y_breakeven": "T2YIE"}},
            clear=False,
        ), mock.patch.object(
            fred, "_request",
            side_effect=_request_stub({"T2YIE": _OBS["T5YIE"]}, captured),
        ):
            inflation_breakevens.get_inflation_breakevens("2025-09-30")
        self.assertEqual(set(captured), {"T2YIE"})

    def test_report_structure_latest_change_and_caveat(self):
        with mock.patch.object(fred, "_request", side_effect=_request_stub()):
            out = inflation_breakevens.get_inflation_breakevens("2025-09-30")
        self.assertIn("## Inflation Breakevens", out)
        self.assertIn("T5YIE", out)
        self.assertIn("T10YIE", out)
        self.assertIn("T5YIFR", out)
        # latest values and change over the window (+0.05 for each stub series)
        self.assertIn("2.45", out)
        self.assertIn("+0.05", out)
        # mandatory caveat: premia, not pure expectations
        self.assertIn("liquidity", out)
        self.assertIn("inflation-risk premia", out)
        self.assertIn("not pure", out.lower())

    def test_missing_value_is_skipped(self):
        with mock.patch.object(fred, "_request", side_effect=_request_stub()):
            out = inflation_breakevens.get_inflation_breakevens("2025-09-30")
        self.assertNotIn("2025-09-03", out)

    def test_empty_series_is_flagged_not_fatal(self):
        obs = dict(_OBS)
        obs["T10YIE"] = {"observations": []}
        with mock.patch.object(fred, "_request", side_effect=_request_stub(obs)):
            out = inflation_breakevens.get_inflation_breakevens("2025-09-30")
        self.assertIn("T10YIE", out)
        self.assertIn("no data", out)
        # the other series still render
        self.assertIn("2.45", out)

    def test_vintage_pinned_to_curr_date(self):
        captured = {}
        with mock.patch.object(fred, "_fred_today", return_value="2026-01-01"), \
                mock.patch.object(fred, "_request", side_effect=_request_stub(captured=captured)):
            inflation_breakevens.get_inflation_breakevens("2025-09-30", 90)
        for series_id, calls in captured.items():
            for _path, params in calls:
                self.assertEqual(params["realtime_start"], "2025-09-30", series_id)
                self.assertEqual(params["realtime_end"], "2025-09-30", series_id)
                self.assertEqual(params["observation_end"], "2025-09-30", series_id)
                self.assertEqual(params["observation_start"], "2025-07-02", series_id)

    def test_future_curr_date_clamps_vintage_to_fred_today(self):
        captured = {}
        with mock.patch.object(fred, "_fred_today", return_value="2026-08-31"), \
                mock.patch.object(fred, "_request", side_effect=_request_stub(captured=captured)):
            inflation_breakevens.get_inflation_breakevens("2026-09-01")
        for series_id, calls in captured.items():
            for _path, params in calls:
                self.assertEqual(params["realtime_start"], "2026-08-31", series_id)
                self.assertEqual(params["realtime_end"], "2026-08-31", series_id)
                self.assertEqual(params["observation_end"], "2026-09-01", series_id)


if __name__ == "__main__":
    unittest.main()
