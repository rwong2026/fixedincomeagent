"""NY Fed GSCPI supply chain pressure vendor.

All HTTP is mocked at the module's ``_request`` boundary, so these run with no
network connection. Caching is exercised against a temp ``data_cache_dir``.
The fixture mirrors the interactive CSV's vintage-matrix shape: first column
``Date`` (observation month-end, ``DD-Mon-YYYY``), then one column per
publication vintage (``Mon-YY``); the LAST vintage column is the current
series. Early vintages have blank tails, and the file ends in a fully blank
trailer row.
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
from fixedincomeagent.dataflows import supply_chain_pressure
from fixedincomeagent.dataflows.config import set_config

# Three vintages; values differ per vintage so the report must reflect the
# LAST (current) one. Older vintages stop early, like the real file.
_FIXTURE = "\n".join(
    [
        "Date,Jan-22,Feb-22,Mar-22",
        "31-Jan-2022,0.33,0.77,0.12",
        "28-Feb-2022,0.44,,0.22",
        "31-Mar-2022,,,0.32",
        "30-Apr-2022,,,-0.10",
        "31-May-2022,,,-0.20",
        ",",  # blank trailer row, as in the real download
    ]
) + "\n"


def _stub(text=None, captured=None):
    body = _FIXTURE if text is None else text

    def _impl(url, params=None):
        if captured is not None:
            captured.append(url)
        return body

    return _impl


class _GscpiTestCase(unittest.TestCase):
    """Redirect the data cache to a temp dir so tests never touch the real one."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        set_config({"data_cache_dir": self._tmp})

    def tearDown(self):
        config_module._config = copy.deepcopy(default_config.DEFAULT_CONFIG)

    def _cache_dir(self):
        return os.path.join(self._tmp, "gscpi")


@pytest.mark.unit
class GscpiParsingTests(_GscpiTestCase):
    def test_returns_markdown(self):
        with mock.patch.object(supply_chain_pressure, "_request", side_effect=_stub()):
            result = supply_chain_pressure.get_supply_chain_pressure("2022-05-15")
        self.assertIsInstance(result, str)
        self.assertIn("Supply Chain Pressure", result)

    def test_report_structure_and_latest_values(self):
        with mock.patch.object(supply_chain_pressure, "_request", side_effect=_stub()):
            out = supply_chain_pressure.get_supply_chain_pressure("2022-05-31")
        self.assertIn("## Global Supply Chain Pressure Index", out)
        self.assertIn("As-of date: 2022-05-31", out)
        # Latest reading on or before the as-of date is May (from the LAST
        # vintage column, Mar-22).
        self.assertIn("2022-05", out)
        self.assertIn("-0.20", out)

    def test_only_last_vintage_leaks(self):
        # Jan-22 holds 0.10/0.20 for Jan/Feb; Mar-22 (current) holds 0.12/0.22.
        # Values from non-current vintages must never appear.
        with mock.patch.object(supply_chain_pressure, "_request", side_effect=_stub()):
            out = supply_chain_pressure.get_supply_chain_pressure("2022-05-15")
        self.assertIn("0.12", out)
        self.assertIn("0.22", out)
        self.assertNotIn("0.33", out)
        self.assertNotIn("0.44", out)
        self.assertNotIn("0.77", out)

    def test_positive_reading_interpretation(self):
        # Latest visible reading (Feb, +0.22) is above the historical average.
        with mock.patch.object(supply_chain_pressure, "_request", side_effect=_stub()):
            out = supply_chain_pressure.get_supply_chain_pressure("2022-02-28")
        self.assertIn("above", out)

    def test_negative_reading_interpretation(self):
        # Latest visible reading (May, -0.20) is below the historical average.
        with mock.patch.object(supply_chain_pressure, "_request", side_effect=_stub()):
            out = supply_chain_pressure.get_supply_chain_pressure("2022-05-31")
        self.assertIn("below", out)

    def test_curr_date_excludes_future_months(self):
        with mock.patch.object(supply_chain_pressure, "_request", side_effect=_stub()):
            out = supply_chain_pressure.get_supply_chain_pressure("2022-02-28")
        self.assertNotIn("2022-03", out)
        self.assertNotIn("2022-04", out)
        self.assertNotIn("2022-05", out)

    def test_no_observations_before_series_start(self):
        with mock.patch.object(supply_chain_pressure, "_request", side_effect=_stub()):
            out = supply_chain_pressure.get_supply_chain_pressure("2022-01-01")
        self.assertIn("No", out)
        self.assertIn("2022-01-01", out)


@pytest.mark.unit
class GscpiFormatErrorTests(_GscpiTestCase):
    def test_html_error_page_errors_loudly(self):
        # The NY Fed site returns a 200 HTML error page for bad paths; that
        # must surface a clear error naming the source, never a false report.
        stub = _stub("<html>Sitecore error page</html>")
        with mock.patch.object(supply_chain_pressure, "_request", side_effect=stub):
            out = supply_chain_pressure.get_supply_chain_pressure("2022-05-15")
        self.assertIn("ERROR", out)
        self.assertIn("New York Fed", out)
        self.assertNotIn("No GSCPI", out)

    def test_no_vintage_columns_errors_loudly(self):
        stub = _stub("Date,Foo\n31-Jan-2022,0.10\n")
        with mock.patch.object(supply_chain_pressure, "_request", side_effect=stub):
            out = supply_chain_pressure.get_supply_chain_pressure("2022-05-15")
        self.assertIn("ERROR", out)
        self.assertIn("New York Fed", out)

    def test_reversed_vintage_labels_error_loudly(self):
        stub = _stub("Date,Mar-22,Jan-22\n31-Jan-2022,0.12,0.10\n")
        with mock.patch.object(supply_chain_pressure, "_request", side_effect=stub):
            out = supply_chain_pressure.get_supply_chain_pressure("2022-05-15")
        self.assertIn("ERROR", out)
        self.assertIn("New York Fed", out)

    def test_non_numeric_value_errors_loudly(self):
        stub = _stub("Date,Jan-22\n31-Jan-2022,abc\n")
        with mock.patch.object(supply_chain_pressure, "_request", side_effect=stub):
            out = supply_chain_pressure.get_supply_chain_pressure("2022-05-15")
        self.assertIn("ERROR", out)
        self.assertIn("New York Fed", out)

    def test_unparseable_observation_date_errors_loudly(self):
        stub = _stub("Date,Jan-22\nJanuary 2022,0.10\n")
        with mock.patch.object(supply_chain_pressure, "_request", side_effect=stub):
            out = supply_chain_pressure.get_supply_chain_pressure("2022-05-15")
        self.assertIn("ERROR", out)
        self.assertIn("New York Fed", out)

    def test_malformed_download_is_not_cached(self):
        stub = _stub("<html>oops</html>")
        with mock.patch.object(supply_chain_pressure, "_request", side_effect=stub):
            supply_chain_pressure.get_supply_chain_pressure("2022-05-15")
        self.assertFalse(os.path.exists(self._cache_dir()))

    def test_network_error_propagates(self):
        with mock.patch.object(
            supply_chain_pressure, "_request",
            side_effect=requests.ConnectionError("boom"),
        ):
            with self.assertRaises(requests.ConnectionError):
                supply_chain_pressure.get_supply_chain_pressure("2022-05-15")


@pytest.mark.unit
class GscpiCacheTests(_GscpiTestCase):
    def test_fresh_cache_is_reused(self):
        with mock.patch.object(
            supply_chain_pressure, "_request", side_effect=_stub()
        ) as m:
            supply_chain_pressure.get_supply_chain_pressure("2022-05-15")
            supply_chain_pressure.get_supply_chain_pressure("2022-05-15")
        self.assertEqual(m.call_count, 1)

    def test_cache_is_written_under_gscpi_dir(self):
        with mock.patch.object(supply_chain_pressure, "_request", side_effect=_stub()):
            supply_chain_pressure.get_supply_chain_pressure("2022-05-15")
        files = os.listdir(self._cache_dir())
        self.assertEqual(len(files), 1)

    def test_stale_cache_is_refetched(self):
        # The series updates monthly; cached files older than 30 days are
        # re-downloaded.
        with mock.patch.object(
            supply_chain_pressure, "_request", side_effect=_stub()
        ) as m:
            supply_chain_pressure.get_supply_chain_pressure("2022-05-15")
            path = os.path.join(self._cache_dir(), os.listdir(self._cache_dir())[0])
            stale = time.time() - 31 * 24 * 3600
            os.utime(path, (stale, stale))
            supply_chain_pressure.get_supply_chain_pressure("2022-05-15")
        self.assertEqual(m.call_count, 2)


if __name__ == "__main__":
    unittest.main()
