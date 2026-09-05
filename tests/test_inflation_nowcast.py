"""Cleveland Fed inflation nowcast vendor.

All HTTP is mocked at the module's ``_request`` boundary, so these run with no
network connection. Caching is exercised against a temp ``data_cache_dir``.
"""
import copy
import json
import os
import tempfile
import time
import unittest
from unittest import mock

import pytest
import requests

import fixedincomeagent.dataflows.config as config_module
import fixedincomeagent.default_config as default_config
from fixedincomeagent.dataflows import inflation_nowcast
from fixedincomeagent.dataflows.config import set_config

_NOWCAST_SERIES = [
    "CPI Inflation",
    "Core CPI Inflation",
    "PCE Inflation",
    "Core PCE Inflation",
]


def _chart(subcaption, labels, columns, with_actuals=True):
    """Build one chart object in the Cleveland Fed webchart JSON shape.

    ``columns`` maps series name -> list of value strings aligned with the
    DAY labels in ``labels`` only ("" = cell blank in the source); release
    markers like "PCE Jul" have no data points in the real file.
    """
    n_days = sum(1 for l in labels if "/" in l)
    dataset = [
        {"seriesname": name, "data": [{"value": v} for v in columns[name]]}
        for name in _NOWCAST_SERIES
        if name in columns
    ]
    if with_actuals:
        # The real file carries "Actual ..." series; the parser must ignore
        # them (they are realized prints, not nowcasts).
        dataset.append(
            {
                "seriesname": "Actual CPI Inflation",
                "data": [{"value": "9.99"} for _ in range(n_days)],
            }
        )
    return {
        "chart": {"subcaption": subcaption},
        "categories": [{"category": [{"label": l} for l in labels]}],
        "dataset": dataset,
    }


# Aug 2026 chart: nowcasts 08/28-09/02, "PCE Jul" vline marker in between,
# CPI values stop once the actual CPI for August is released (09/02).
_AUG = _chart(
    "2026-8",
    ["08/28", "08/29", "PCE Jul", "09/01", "09/02"],
    {
        "CPI Inflation": ["0.36111", "0.36222", "0.36333", ""],
        "Core CPI Inflation": ["0.20111", "0.20222", "0.20333", ""],
        "PCE Inflation": ["0.35111", "0.35222", "0.35333", "0.35444"],
        "Core PCE Inflation": ["0.27111", "0.27222", "0.27333", "0.27444"],
    },
)

# Sep 2026 chart: fresh month, nowcasts start 09/01.
_SEP = _chart(
    "2026-9",
    ["09/01", "09/02", "09/03"],
    {
        "CPI Inflation": ["0.38111", "0.38222", "0.38333"],
        "Core CPI Inflation": ["0.19111", "0.19222", "0.19333"],
        "PCE Inflation": ["0.37111", "0.37222", "0.37333"],
        "Core PCE Inflation": ["0.28111", "0.28222", "0.28333"],
    },
)

# Dec 2025 chart crossing the year boundary: 01/xx labels belong to 2026.
_DEC = _chart(
    "2025-12",
    ["12/30", "12/31", "01/02"],
    {
        "CPI Inflation": ["0.30111", "0.30222", "0.30333"],
        "Core CPI Inflation": ["0.25111", "0.25222", "0.25333"],
        "PCE Inflation": ["0.29111", "0.29222", "0.29333"],
        "Core PCE Inflation": ["0.26111", "0.26222", "0.26333"],
    },
)


def _payload(*charts):
    return json.dumps(list(charts))


def _stub(text=None, captured=None):
    body = _payload(_AUG, _SEP) if text is None else text

    def _impl(url, params=None):
        if captured is not None:
            captured.append(url)
        return body

    return _impl


class _NowcastTestCase(unittest.TestCase):
    """Redirect the data cache to a temp dir so tests never touch the real one."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        set_config({"data_cache_dir": self._tmp})

    def tearDown(self):
        config_module._config = copy.deepcopy(default_config.DEFAULT_CONFIG)

    def _cache_dir(self):
        return os.path.join(self._tmp, "cleveland_fed")


@pytest.mark.unit
class NowcastParsingTests(_NowcastTestCase):
    def test_returns_markdown(self):
        with mock.patch.object(inflation_nowcast, "_request", side_effect=_stub()):
            result = inflation_nowcast.get_inflation_nowcast("2026-09-03")
        self.assertIsInstance(result, str)
        self.assertIn("Inflation Nowcast", result)

    def test_report_structure_and_latest_values(self):
        with mock.patch.object(inflation_nowcast, "_request", side_effect=_stub()):
            out = inflation_nowcast.get_inflation_nowcast("2026-09-03")
        self.assertIn("## Cleveland Fed Inflation Nowcasting", out)
        self.assertIn("As-of date: 2026-09-03", out)
        # Latest nowcast per open month (latest in-window day = 09/03), values
        # rounded to 2 decimals like the Cleveland Fed website tables. Aug CPI
        # nowcasts stop at 09/02 (actual released), so the final pre-release
        # nowcast (0.36333) is the latest available.
        self.assertIn("| 2026-09 | 0.38 | 0.19 | 0.37 | 0.28 |", out)
        self.assertIn("| 2026-08 | 0.36 | 0.20 | 0.35 | 0.27 |", out)

    def test_daily_table_lists_nowcast_dates(self):
        with mock.patch.object(inflation_nowcast, "_request", side_effect=_stub()):
            out = inflation_nowcast.get_inflation_nowcast("2026-09-03")
        self.assertIn("| 2026-09-01 | 2026-09 |", out)
        self.assertIn("| 2026-09-02 | 2026-09 |", out)
        daily = out[out.index("| Nowcast date |"):]
        self.assertLess(daily.index("2026-09-01"), daily.index("2026-09-03"))

    def test_actual_series_do_not_leak(self):
        # The canned "Actual ..." cells all hold 9.99; realized prints must
        # never appear in a nowcast report.
        with mock.patch.object(inflation_nowcast, "_request", side_effect=_stub()):
            out = inflation_nowcast.get_inflation_nowcast("2026-09-03")
        self.assertNotIn("9.99", out)
        self.assertNotIn("Actual", out)

    def test_curr_date_excludes_future_nowcasts(self):
        # 09/02-09/03 nowcasts are in the future relative to 2026-09-01.
        with mock.patch.object(inflation_nowcast, "_request", side_effect=_stub()):
            out = inflation_nowcast.get_inflation_nowcast("2026-09-01")
        self.assertNotIn("2026-09-02", out)
        self.assertNotIn("2026-09-03", out)
        # The Sep month row reflects only the 09/01 snapshot (0.38111 -> 0.38).
        self.assertIn("| 2026-09 | 0.38 | 0.19 | 0.37 | 0.28 |", out)

    def test_vline_markers_are_not_data_rows(self):
        with mock.patch.object(inflation_nowcast, "_request", side_effect=_stub()):
            out = inflation_nowcast.get_inflation_nowcast("2026-09-03")
        self.assertNotIn("PCE Jul", out)

    def test_year_rollover_in_labels(self):
        stub = _stub(_payload(_DEC))
        with mock.patch.object(inflation_nowcast, "_request", side_effect=stub):
            out = inflation_nowcast.get_inflation_nowcast("2026-01-05")
        # 01/02 in the 2025-12 chart is 2026-01-02, not 2025-01-02.
        self.assertIn("2026-01-02", out)
        self.assertNotIn("2025-01-02", out)

    def test_year_rollover_respects_curr_date(self):
        stub = _stub(_payload(_DEC))
        with mock.patch.object(inflation_nowcast, "_request", side_effect=stub):
            out = inflation_nowcast.get_inflation_nowcast("2025-12-31")
        self.assertIn("2025-12-31", out)
        self.assertNotIn("2026-01-02", out)

    def test_no_observations_before_first_nowcast(self):
        stub = _stub(_payload(_SEP))
        with mock.patch.object(inflation_nowcast, "_request", side_effect=stub):
            out = inflation_nowcast.get_inflation_nowcast("2020-01-01")
        self.assertIn("No", out)
        self.assertIn("2020-01-01", out)


@pytest.mark.unit
class NowcastFormatErrorTests(_NowcastTestCase):
    def test_html_error_page_errors_loudly(self):
        # A 200 with a changed body must surface a clear error naming the
        # source — never a false "no data" report.
        stub = _stub("<html>Sitecore error page</html>")
        with mock.patch.object(inflation_nowcast, "_request", side_effect=stub):
            out = inflation_nowcast.get_inflation_nowcast("2026-09-03")
        self.assertIn("ERROR", out)
        self.assertIn("Cleveland Fed", out)
        self.assertNotIn("No Cleveland Fed nowcast observations", out)

    def test_missing_series_errors_loudly(self):
        bad = _chart(
            "2026-9",
            ["09/01"],
            {
                "CPI Inflation": ["0.38"],
                "Core CPI Inflation": ["0.19"],
                "PCE Inflation": ["0.37"],
                # Core PCE Inflation dropped -> shape changed
            },
        )
        stub = _stub(json.dumps([bad]))
        with mock.patch.object(inflation_nowcast, "_request", side_effect=stub):
            out = inflation_nowcast.get_inflation_nowcast("2026-09-03")
        self.assertIn("ERROR", out)
        self.assertIn("Cleveland Fed", out)

    def test_malformed_download_is_not_cached(self):
        stub = _stub("<html>oops</html>")
        with mock.patch.object(inflation_nowcast, "_request", side_effect=stub):
            inflation_nowcast.get_inflation_nowcast("2026-09-03")
        self.assertFalse(os.path.exists(self._cache_dir()))

    def test_network_error_propagates(self):
        with mock.patch.object(
            inflation_nowcast, "_request",
            side_effect=requests.ConnectionError("boom"),
        ):
            with self.assertRaises(requests.ConnectionError):
                inflation_nowcast.get_inflation_nowcast("2026-09-03")


@pytest.mark.unit
class NowcastCacheTests(_NowcastTestCase):
    def test_fresh_cache_is_reused(self):
        with mock.patch.object(
            inflation_nowcast, "_request", side_effect=_stub()
        ) as m:
            inflation_nowcast.get_inflation_nowcast("2026-09-03")
            inflation_nowcast.get_inflation_nowcast("2026-09-03")
        self.assertEqual(m.call_count, 1)

    def test_cache_is_written_under_cleveland_fed_dir(self):
        with mock.patch.object(inflation_nowcast, "_request", side_effect=_stub()):
            inflation_nowcast.get_inflation_nowcast("2026-09-03")
        files = os.listdir(self._cache_dir())
        self.assertEqual(len(files), 1)

    def test_stale_cache_is_refetched(self):
        with mock.patch.object(
            inflation_nowcast, "_request", side_effect=_stub()
        ) as m:
            inflation_nowcast.get_inflation_nowcast("2026-09-03")
            # Age the cache file past the 24h TTL.
            path = os.path.join(self._cache_dir(), os.listdir(self._cache_dir())[0])
            stale = time.time() - 25 * 3600
            os.utime(path, (stale, stale))
            inflation_nowcast.get_inflation_nowcast("2026-09-03")
        self.assertEqual(m.call_count, 2)


if __name__ == "__main__":
    unittest.main()
