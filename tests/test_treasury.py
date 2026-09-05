"""Treasury.gov vendor: par yield curve and auction results.

All HTTP is mocked at the module's ``_request`` boundary, so these run with no
network connection. Caching is exercised against a temp ``data_cache_dir``.
"""
import copy
import json
import tempfile
import unittest
from datetime import date
from unittest import mock

import pytest

import fixedincomeagent.dataflows.config as config_module
import fixedincomeagent.default_config as default_config
from fixedincomeagent.dataflows import treasury
from fixedincomeagent.dataflows.config import set_config

_PAR_CSV_2023 = """Date,"1 Mo","2 Mo","3 Mo","4 Mo","6 Mo","1 Yr","2 Yr","3 Yr","5 Yr","7 Yr","10 Yr","20 Yr","30 Yr"
12/29/2023,5.60,5.59,5.40,5.41,5.26,4.79,4.23,4.01,3.84,3.88,3.88,4.20,4.03
11/16/2023,5.56,5.54,5.44,5.46,5.40,4.90,4.55,4.35,4.20,4.15,4.10,4.30,4.10
11/15/2023,5.55,5.53,5.43,5.45,5.39,4.89,4.54,4.34,4.19,4.14,4.09,4.29,4.09
"""

_PAR_CSV_2024 = """Date,"1 Mo","2 Mo","3 Mo","4 Mo","6 Mo","1 Yr","2 Yr","3 Yr","5 Yr","7 Yr","10 Yr","20 Yr","30 Yr"
12/31/2024,4.40,4.39,4.37,4.32,4.24,4.16,4.25,4.27,4.38,4.48,4.58,4.86,4.78
06/14/2024,5.40,5.39,5.38,5.37,5.25,5.17,4.70,4.50,4.35,4.40,4.20,4.50,4.34
06/13/2024,5.41,5.40,5.39,5.38,5.26,5.18,4.71,4.51,4.36,4.41,4.22,4.51,4.35
01/02/2024,5.50,5.48,5.40,5.42,5.30,4.80,4.30,4.10,3.95,3.90,3.95,4.15,4.00
"""

_EMPTY_CSV = 'Date,"1 Mo","2 Mo","3 Mo"\n'

_AUCTIONS = {
    "data": [
        {
            "auction_date": "2024-06-12",
            "cusip": "912810TU0",
            "security_type": "Bond",
            "security_term": "30-Year",
            # announced but not yet priced -> must be dropped
            "high_yield": "null",
            "high_investment_rate": "null",
            "bid_to_cover_ratio": "null",
            "offering_amt": "22000000000",
        },
        {
            "auction_date": "2024-06-11",
            "cusip": "91282CKP5",
            "security_type": "Note",
            "security_term": "10-Year",
            "high_yield": "4.438",
            "high_investment_rate": "null",
            "bid_to_cover_ratio": "2.490000",
            "offering_amt": "39000000000",
        },
        {
            "auction_date": "2024-06-06",
            "cusip": "912797LV6",
            "security_type": "Bill",
            "security_term": "4-Week",
            "high_yield": "null",
            "high_investment_rate": "5.285",
            "bid_to_cover_ratio": "2.900000",
            "offering_amt": "90000000000",
        },
    ]
}


def _request_stub(csv_by_year=None, auctions=_AUCTIONS, captured=None):
    """Build a treasury._request replacement dispatching on the URL."""
    csv_by_year = csv_by_year if csv_by_year is not None else {"2024": _PAR_CSV_2024}

    def _impl(url, params=None):
        if captured is not None:
            captured.append((url, dict(params or {})))
        if "daily-treasury-rates.csv" in url:
            return csv_by_year[params["field_tdr_date_value"]]
        if "auctions_query" in url:
            return json.dumps(auctions)
        raise AssertionError(f"unexpected URL: {url}")

    return _impl


class _TreasuryTestCase(unittest.TestCase):
    """Redirect the data cache to a temp dir so tests never touch the real one."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        set_config({"data_cache_dir": self._tmp})

    def tearDown(self):
        config_module._config = copy.deepcopy(default_config.DEFAULT_CONFIG)


@pytest.mark.unit
class ParYieldFormattingTests(_TreasuryTestCase):
    def test_returns_markdown(self):
        # Brief smoke test, adapted to run offline.
        with mock.patch.object(treasury, "_request", side_effect=_request_stub()):
            result = treasury.get_treasury_par_yields("2024-06-15", look_back_days=30)
        self.assertIsInstance(result, str)
        self.assertTrue(
            "Treasury" in result or "Par Yield" in result or "CMT" in result
        )

    def test_report_has_header_latest_curve_and_daily_table(self):
        with mock.patch.object(treasury, "_request", side_effect=_request_stub()):
            out = treasury.get_treasury_par_yields("2024-06-15", look_back_days=30)
        self.assertIn("## Treasury Par Yield Curve", out)
        self.assertIn("CMT", out)
        self.assertIn("Window: 2024-05-16 to 2024-06-15", out)
        # latest in-window snapshot is the last business day <= curr_date
        self.assertIn("Latest curve (2024-06-14)", out)
        self.assertIn("| 10 Yr | 4.20 |", out)
        # daily table carries the recent observations, oldest first
        self.assertIn("| 2024-06-13 |", out)
        daily = out[out.index("| Date |"):]
        self.assertLess(daily.index("2024-06-13"), daily.index("2024-06-14"))

    def test_change_over_window_uses_first_and_last_observation(self):
        with mock.patch.object(treasury, "_request", side_effect=_request_stub()):
            out = treasury.get_treasury_par_yields("2024-06-15", look_back_days=30)
        # 2 Yr: 4.71 (06/13) -> 4.70 (06/14); 10 Yr: 4.22 -> 4.20
        self.assertIn("2 Yr: 4.71 -> 4.70 (-0.01)", out)
        self.assertIn("10 Yr: 4.22 -> 4.20 (-0.02)", out)

    def test_window_is_lookahead_safe(self):
        # Rows dated after curr_date (12/31/2024 in the canned CSV) never appear.
        with mock.patch.object(treasury, "_request", side_effect=_request_stub()):
            out = treasury.get_treasury_par_yields("2024-06-15", look_back_days=30)
        self.assertNotIn("2024-12-31", out)
        self.assertNotIn("4.78", out)

    def test_rows_before_window_start_are_excluded(self):
        # 01/02/2024 predates the 30-day window ending 2024-06-15.
        with mock.patch.object(treasury, "_request", side_effect=_request_stub()):
            out = treasury.get_treasury_par_yields("2024-06-15", look_back_days=30)
        self.assertNotIn("2024-01-02", out)

    def test_empty_window_reports_no_observations(self):
        stub = _request_stub(csv_by_year={"2024": _EMPTY_CSV})
        with mock.patch.object(treasury, "_request", side_effect=stub):
            out = treasury.get_treasury_par_yields("2024-06-15", look_back_days=30)
        self.assertIn("No", out)
        self.assertIn("window", out)


@pytest.mark.unit
class ParYieldFetchingTests(_TreasuryTestCase):
    def test_fetches_each_year_the_window_touches(self):
        captured = []
        stub = _request_stub(
            csv_by_year={"2023": _PAR_CSV_2023, "2024": _PAR_CSV_2024},
            captured=captured,
        )
        # 60 days back from 2024-01-15 crosses the year boundary into 2023.
        with mock.patch.object(treasury, "_request", side_effect=stub):
            out = treasury.get_treasury_par_yields("2024-01-15", look_back_days=60)
        years = {p["field_tdr_date_value"] for _, p in captured}
        self.assertEqual(years, {"2023", "2024"})
        # 2023 rows inside the window are included.
        self.assertIn("2023-12-29", out)

    def test_past_year_csv_is_cached(self):
        stub = _request_stub(csv_by_year={"2023": _PAR_CSV_2023})
        with mock.patch.object(treasury, "_request", side_effect=stub) as m:
            treasury.get_treasury_par_yields("2023-12-31", look_back_days=30)
            treasury.get_treasury_par_yields("2023-12-31", look_back_days=30)
        self.assertEqual(m.call_count, 1)  # second call served from cache

    def test_current_year_csv_is_not_cached(self):
        # The current-year feed is still updating intraday, so it is refetched.
        year = str(date.today().year)
        csv_text = _PAR_CSV_2024.replace("2024", year)
        stub = _request_stub(csv_by_year={year: csv_text})
        curr = f"{year}-06-15"
        with mock.patch.object(treasury, "_request", side_effect=stub) as m:
            treasury.get_treasury_par_yields(curr, look_back_days=30)
            treasury.get_treasury_par_yields(curr, look_back_days=30)
        self.assertEqual(m.call_count, 2)


@pytest.mark.unit
class AuctionResultsTests(_TreasuryTestCase):
    def test_returns_markdown(self):
        # Brief smoke test, adapted to run offline.
        with mock.patch.object(treasury, "_request", side_effect=_request_stub()):
            result = treasury.get_auction_results("2024-06-15", look_back_days=60)
        self.assertIsInstance(result, str)

    def test_report_structure_and_rows(self):
        with mock.patch.object(treasury, "_request", side_effect=_request_stub()):
            out = treasury.get_auction_results("2024-06-15", look_back_days=60)
        self.assertIn("## Treasury Auction Results", out)
        self.assertIn("Window: 2024-04-16 to 2024-06-15", out)
        self.assertIn("| 2024-06-11 | 10-Year Note | 91282CKP5 | 4.438 | 2.49 | 39.0 |", out)
        # a Bill row falls back to its investment rate when high_yield is null
        self.assertIn("| 2024-06-06 | 4-Week Bill | 912797LV6 | 5.285 | 2.90 | 90.0 |", out)
        # most recent results first
        self.assertLess(out.index("2024-06-11"), out.index("2024-06-06"))

    def test_unpriced_announced_auction_is_dropped(self):
        with mock.patch.object(treasury, "_request", side_effect=_request_stub()):
            out = treasury.get_auction_results("2024-06-15", look_back_days=60)
        self.assertNotIn("912810TU0", out)

    def test_date_window_params(self):
        captured = []
        with mock.patch.object(
            treasury, "_request", side_effect=_request_stub(captured=captured)
        ):
            treasury.get_auction_results("2024-06-15", look_back_days=90)
        self.assertEqual(len(captured), 1)
        _, params = captured[0]
        self.assertEqual(
            params["filter"],
            "auction_date:gte:2024-03-17,auction_date:lte:2024-06-15",
        )

    def test_empty_window_reports_no_results(self):
        stub = _request_stub(auctions={"data": []})
        with mock.patch.object(treasury, "_request", side_effect=stub):
            out = treasury.get_auction_results("2024-06-15", look_back_days=30)
        self.assertIn("No auction", out)


if __name__ == "__main__":
    unittest.main()
