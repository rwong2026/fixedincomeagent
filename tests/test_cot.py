"""CFTC COT (Traders in Financial Futures) Treasury futures positioning vendor.

All HTTP is mocked at the module's ``_request`` boundary, so these run with no
network connection. Caching is exercised against a temp ``data_cache_dir``.
The fixture mirrors the real Socrata ``gpe5-46if`` response shape: a JSON list
of row dicts, newest report first, with all numeric values as strings. Only
the columns the module selects are present; each category carries distinct
values so a long/short mix-up would leak detectably wrong numbers.
"""
import copy
import os
import tempfile
import time
import unittest
from unittest import mock

import pytest
import requests

import fixedincomeagent.dataflows.config as config_module
import fixedincomeagent.default_config as default_config
from fixedincomeagent.dataflows import cot_data
from fixedincomeagent.dataflows.config import set_config


# Three weekly TFF rows, newest first, as the Socrata API returns them.
def _row(date, oi, d_long, d_short, am_long, am_short, lm_long, lm_short):
    return {
        "report_date_as_yyyy_mm_dd": f"{date}T00:00:00.000",
        "market_and_exchange_names": "UST 10Y NOTE - CHICAGO BOARD OF TRADE",
        "open_interest_all": str(oi),
        "dealer_positions_long_all": str(d_long),
        "dealer_positions_short_all": str(d_short),
        "asset_mgr_positions_long": str(am_long),
        "asset_mgr_positions_short": str(am_short),
        "lev_money_positions_long": str(lm_long),
        "lev_money_positions_short": str(lm_short),
    }


_PAYLOAD = [
    _row("2026-09-01", 2500000, 80000, 320000, 1250000, 530000, 155000, 575000),
    _row("2026-08-25", 2450000, 75000, 315000, 1240000, 520000, 150000, 565000),
    _row("2026-08-18", 2400000, 70000, 310000, 1230000, 510000, 145000, 555000),
]


def _stub(payload=None):
    body = _PAYLOAD if payload is None else payload

    def _impl(url, params):
        return body

    return _impl


class _CotTestCase(unittest.TestCase):
    """Redirect the data cache to a temp dir so tests never touch the real one."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        set_config({"data_cache_dir": self._tmp})

    def tearDown(self):
        config_module._config = copy.deepcopy(default_config.DEFAULT_CONFIG)

    def _cache_dir(self):
        return os.path.join(self._tmp, "cftc_cot")


@pytest.mark.unit
class CotReportTests(_CotTestCase):
    def test_returns_markdown_with_header(self):
        with mock.patch.object(cot_data, "_request", side_effect=_stub()):
            result = cot_data.get_cot_data("2026-09-05")
        self.assertIsInstance(result, str)
        self.assertIn("## CFTC COT Positioning", result)
        self.assertIn("10-Year U.S. Treasury Note", result)
        self.assertIn("As-of date: 2026-09-05", result)

    def test_latest_report_net_positions(self):
        # Latest row (2026-09-01): Dealer 80k-320k=-240,000; AM 1250k-530k=+720,000;
        # LM 155k-575k=-420,000; OI 2,500,000.
        with mock.patch.object(cot_data, "_request", side_effect=_stub()):
            out = cot_data.get_cot_data("2026-09-05")
        self.assertIn("2026-09-01", out)
        self.assertIn("2,500,000", out)
        self.assertIn("-240,000", out)
        self.assertIn("+720,000", out)
        self.assertIn("-420,000", out)

    def test_week_over_week_change(self):
        # Dealer net went -240,000 (09-01) from -240,000 (08-25: 75k-315k) -> 0;
        # LM net went -420,000 from -415,000 -> -5,000.
        with mock.patch.object(cot_data, "_request", side_effect=_stub()):
            out = cot_data.get_cot_data("2026-09-05")
        self.assertIn("unchanged", out)
        self.assertIn("-5,000", out)

    def test_recent_weeks_table(self):
        with mock.patch.object(cot_data, "_request", side_effect=_stub()):
            out = cot_data.get_cot_data("2026-09-05")
        self.assertIn("| Report date |", out)
        self.assertIn("| 2026-08-25 |", out)
        self.assertIn("| 2026-08-18 |", out)

    def test_point_in_time_filtering(self):
        # As-of 2026-08-27: the 2026-09-01 report must not be visible.
        with mock.patch.object(cot_data, "_request", side_effect=_stub()):
            out = cot_data.get_cot_data("2026-08-27")
        self.assertNotIn("2026-09-01", out)
        self.assertIn("2026-08-25", out)

    def test_no_reports_on_or_before_curr_date(self):
        with mock.patch.object(cot_data, "_request", side_effect=_stub()):
            out = cot_data.get_cot_data("2026-08-01")
        self.assertIn("No", out)
        self.assertIn("2026-08-01", out)

    def test_default_contract_queries_10y_code(self):
        with mock.patch.object(
            cot_data, "_request", side_effect=_stub()
        ) as m:
            cot_data.get_cot_data("2026-09-05")
        params = m.call_args.args[1]
        self.assertIn("043602", params["$where"])

    def test_contract_selection_maps_to_cftc_code(self):
        with mock.patch.object(
            cot_data, "_request", side_effect=_stub()
        ) as m:
            cot_data.get_cot_data("2026-09-05", contract="UST_2Y")
        params = m.call_args.args[1]
        self.assertIn("042601", params["$where"])

    def test_contract_mapping_contents(self):
        # Verified 2026-09-05 against the Socrata dataset's distinct codes:
        # 020601 is the classic 30Y bond ("UST BOND" since Feb 2022), 020604
        # the separate Ultra Bond ("ULTRA UST BOND").
        self.assertEqual(
            cot_data.CONTRACTS,
            {
                "UST_2Y": ("042601", "2-Year U.S. Treasury Note futures"),
                "UST_5Y": ("044601", "5-Year U.S. Treasury Note futures"),
                "UST_10Y": ("043602", "10-Year U.S. Treasury Note futures"),
                "UST_30Y": ("020601", "30-Year U.S. Treasury Bond futures"),
                "UST_ULTRA": ("020604", "Ultra U.S. Treasury Bond futures"),
            },
        )

    def test_server_side_date_filter(self):
        with mock.patch.object(
            cot_data, "_request", side_effect=_stub()
        ) as m:
            cot_data.get_cot_data("2026-08-27")
        params = m.call_args.args[1]
        self.assertIn("report_date_as_yyyy_mm_dd <= '2026-08-27'", params["$where"])

    def test_unknown_contract_raises_value_error(self):
        with self.assertRaises(ValueError) as ctx:
            cot_data.get_cot_data("2026-09-05", contract="BANANA")
        self.assertIn("UST_10Y", str(ctx.exception))


@pytest.mark.unit
class CotFormatErrorTests(_CotTestCase):
    def _get(self, payload):
        with mock.patch.object(cot_data, "_request", side_effect=_stub(payload)):
            return cot_data.get_cot_data("2026-09-05")

    def test_socrata_error_body_errors_loudly(self):
        out = self._get({"error": True, "message": "query.compiler.malformed"})
        self.assertIn("ERROR", out)
        self.assertIn("CFTC", out)

    def test_missing_field_errors_loudly(self):
        payload = [dict(r) for r in _PAYLOAD]
        del payload[0]["lev_money_positions_short"]
        out = self._get(payload)
        self.assertIn("ERROR", out)
        self.assertIn("CFTC", out)

    def test_non_numeric_position_errors_loudly(self):
        payload = [dict(r) for r in _PAYLOAD]
        payload[0]["asset_mgr_positions_long"] = "n/a"
        out = self._get(payload)
        self.assertIn("ERROR", out)
        self.assertIn("CFTC", out)

    def test_bad_report_date_errors_loudly(self):
        payload = [dict(r) for r in _PAYLOAD]
        payload[0]["report_date_as_yyyy_mm_dd"] = "09/01/2026"
        out = self._get(payload)
        self.assertIn("ERROR", out)
        self.assertIn("CFTC", out)

    def test_out_of_order_rows_error_loudly(self):
        out = self._get([_PAYLOAD[1], _PAYLOAD[0], _PAYLOAD[2]])
        self.assertIn("ERROR", out)
        self.assertIn("CFTC", out)

    def test_malformed_response_is_not_cached(self):
        self._get({"error": True})
        self.assertFalse(os.path.exists(self._cache_dir()))

    def test_network_error_propagates(self):
        with mock.patch.object(
            cot_data,
            "_request",
            side_effect=requests.ConnectionError("boom"),
        ), self.assertRaises(requests.ConnectionError):
            cot_data.get_cot_data("2026-09-05")


@pytest.mark.unit
class CotCacheTests(_CotTestCase):
    def test_fresh_cache_is_reused(self):
        with mock.patch.object(cot_data, "_request", side_effect=_stub()) as m:
            cot_data.get_cot_data("2026-09-05")
            cot_data.get_cot_data("2026-09-05")
        self.assertEqual(m.call_count, 1)

    def test_cache_is_written_under_cftc_cot_dir(self):
        with mock.patch.object(cot_data, "_request", side_effect=_stub()):
            cot_data.get_cot_data("2026-09-05")
        files = os.listdir(self._cache_dir())
        self.assertEqual(len(files), 1)
        self.assertTrue(files[0].endswith(".json"))

    def test_cached_file_round_trips(self):
        with mock.patch.object(cot_data, "_request", side_effect=_stub()):
            fresh = cot_data.get_cot_data("2026-09-05")
        with mock.patch.object(cot_data, "_request") as m:
            cached = cot_data.get_cot_data("2026-09-05")
        m.assert_not_called()
        self.assertEqual(fresh, cached)

    def test_stale_cache_is_refetched(self):
        # The report updates weekly; cached files older than 7 days are
        # re-downloaded.
        with mock.patch.object(cot_data, "_request", side_effect=_stub()) as m:
            cot_data.get_cot_data("2026-09-05")
            path = os.path.join(self._cache_dir(), os.listdir(self._cache_dir())[0])
            stale = time.time() - 8 * 24 * 3600
            os.utime(path, (stale, stale))
            cot_data.get_cot_data("2026-09-05")
        self.assertEqual(m.call_count, 2)

    def test_corrupt_cache_is_refetched(self):
        with mock.patch.object(cot_data, "_request", side_effect=_stub()) as m:
            cot_data.get_cot_data("2026-09-05")
            path = os.path.join(self._cache_dir(), os.listdir(self._cache_dir())[0])
            with open(path, "w") as f:
                f.write("{not json")
            out = cot_data.get_cot_data("2026-09-05")
        self.assertEqual(m.call_count, 2)
        self.assertIn("## CFTC COT Positioning", out)


if __name__ == "__main__":
    unittest.main()
