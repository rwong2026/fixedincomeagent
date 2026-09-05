"""NY Fed Survey of Consumer Expectations: median inflation expectations vendor.

All HTTP is mocked at the module's ``_request`` boundary, so these run with no
network connection. Caching is exercised against a temp ``data_cache_dir``.
The fixture mirrors the real ``frbny-sce-data.xlsx`` shape: per sheet, a source
row, a title row, a blank row, then a header row whose first cell is empty,
then monthly rows keyed by an integer ``YYYYMM``. The "Inflation expectations"
sheet carries the median one- and three-year ahead rates (plus percentile
columns the module must ignore); "Five-year ahead Infl Exp" carries the median
five-year ahead rate (series starts 2022-01 in the real file).
"""
import copy
import io
import os
import tempfile
import time
import unittest
from unittest import mock

import openpyxl
import pytest
import requests

import fixedincomeagent.dataflows.config as config_module
import fixedincomeagent.default_config as default_config
from fixedincomeagent.dataflows import consumer_inflation_expectations
from fixedincomeagent.dataflows.config import set_config

_INFL_HEADER = [
    None,
    "Median one-year ahead expected inflation rate",
    "Median three-year ahead expected inflation rate",
    "25th Percentile one-year ahead expected inflation rate",
    "25th Percentile three-year ahead expected inflation rate",
    "75th Percentile one-year ahead expected inflation rate",
    "75th Percentile three-year ahead expected inflation rate",
    "Median point prediction one-year ahead inflation rate",
    "Median point prediction three-year ahead inflation rate",
]
_FIVE_YEAR_HEADER = [
    None,
    "Median five-year ahead expected inflation rate",
    "25th Percentile five-year ahead expected inflation rate",
    "75th Percentile five-year ahead expected inflation rate",
    "Median point prediction five-year ahead inflation rate",
    "Median five-year ahead uncertainty",
]

# (YYYYMM, 1yr median, 3yr median); percentile cells filled with distinct
# values so a column mix-up would leak detectably wrong numbers.
_INFL_ROWS = [
    (202112, 2.9, 3.0, 1.01, 1.11, 5.01, 5.11, 4.01, 4.11),
    (202201, 3.0, 3.1, 1.02, 1.12, 5.02, 5.12, 4.02, 4.12),
    (202202, 3.2, 3.3, 1.03, 1.13, 5.03, 5.13, 4.03, 4.13),
    (202203, 3.4, 3.5, 1.04, 1.14, 5.04, 5.14, 4.04, 4.14),
    (202204, 3.6, 3.7, 1.05, 1.15, 5.05, 5.15, 4.05, 4.15),
    (202205, 3.8, 3.9, 1.06, 1.16, 5.06, 5.16, 4.06, 4.16),
]
# (YYYYMM, 5yr median); starts 2022-01 like the real series.
_FIVE_YEAR_ROWS = [
    (202201, 2.5, 0.5, 6.5, 3.5, 2.5),
    (202202, 2.6, 0.6, 6.6, 3.6, 2.6),
    (202203, 2.7, 0.7, 6.7, 3.7, 2.7),
    (202204, 2.8, 0.8, 6.8, 3.8, 2.8),
    (202205, 2.9, 0.9, 6.9, 3.9, 2.9),
]


def _sheet(ws, title, header, rows):
    ws.append(["Source: Survey of Consumer Expectations, FRBNY."])
    ws.append([title])
    ws.append([])
    ws.append(header)
    for row in rows:
        ws.append(list(row))


def _build_xlsx(infl_rows=_INFL_ROWS, five_year_rows=_FIVE_YEAR_ROWS,
                infl_header=_INFL_HEADER, five_year_header=_FIVE_YEAR_HEADER,
                include_five_year_sheet=True):
    wb = openpyxl.Workbook()
    _sheet(wb.active, "Inflation expectations", infl_header, infl_rows)
    wb.active.title = "Inflation expectations"
    if include_five_year_sheet:
        _sheet(
            wb.create_sheet("Five-year ahead Infl Exp"),
            "Five-year ahead inflation expectations",
            five_year_header,
            five_year_rows,
        )
    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


_FIXTURE = _build_xlsx()


def _stub(content=None):
    body = _FIXTURE if content is None else content

    def _impl(url, params=None):
        return body

    return _impl


class _SceTestCase(unittest.TestCase):
    """Redirect the data cache to a temp dir so tests never touch the real one."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        set_config({"data_cache_dir": self._tmp})

    def tearDown(self):
        config_module._config = copy.deepcopy(default_config.DEFAULT_CONFIG)

    def _cache_dir(self):
        return os.path.join(self._tmp, "ny_fed_sce")


@pytest.mark.unit
class SceParsingTests(_SceTestCase):
    def test_returns_markdown(self):
        with mock.patch.object(
            consumer_inflation_expectations, "_request", side_effect=_stub()
        ):
            result = consumer_inflation_expectations.get_consumer_inflation_expectations(
                "2022-05-31"
            )
        self.assertIsInstance(result, str)
        self.assertIn("Consumer Inflation Expectations", result)

    def test_report_structure_and_latest_values(self):
        with mock.patch.object(
            consumer_inflation_expectations, "_request", side_effect=_stub()
        ):
            out = consumer_inflation_expectations.get_consumer_inflation_expectations(
                "2022-05-31"
            )
        self.assertIn("## Consumer Inflation Expectations", out)
        self.assertIn("As-of date: 2022-05-31", out)
        # Latest survey month medians: 1yr 3.8, 3yr 3.9, 5yr 2.9.
        self.assertIn("2022-05", out)
        self.assertIn("3.80", out)
        self.assertIn("3.90", out)
        self.assertIn("2.90", out)

    def test_only_median_columns_leak(self):
        # Percentile / point-prediction columns hold distinct values (5.x, 4.x,
        # 1.x); the report must contain only the median columns.
        with mock.patch.object(
            consumer_inflation_expectations, "_request", side_effect=_stub()
        ):
            out = consumer_inflation_expectations.get_consumer_inflation_expectations(
                "2022-05-31"
            )
        for leaked in ("5.06", "5.16", "4.06", "4.16", "1.06", "1.16", "6.90"):
            self.assertNotIn(leaked, out)

    def test_five_year_blank_before_series_start(self):
        # The five-year series starts 2022-01 in the real file; the 2021-12
        # row must render an empty five-year cell, not a fabricated value.
        with mock.patch.object(
            consumer_inflation_expectations, "_request", side_effect=_stub()
        ):
            out = consumer_inflation_expectations.get_consumer_inflation_expectations(
                "2022-05-31"
            )
        self.assertIn("| 2021-12 | 2.90 | 3.00 |  |", out)

    def test_trend_line(self):
        # Latest 1yr median (2022-05: 3.8) vs three months earlier (3.2): +0.6pp.
        with mock.patch.object(
            consumer_inflation_expectations, "_request", side_effect=_stub()
        ):
            out = consumer_inflation_expectations.get_consumer_inflation_expectations(
                "2022-05-31"
            )
        self.assertIn("0.60", out)

    def test_curr_date_excludes_future_months(self):
        with mock.patch.object(
            consumer_inflation_expectations, "_request", side_effect=_stub()
        ):
            out = consumer_inflation_expectations.get_consumer_inflation_expectations(
                "2022-03-31"
            )
        self.assertNotIn("2022-04", out)
        self.assertNotIn("2022-05", out)
        self.assertIn("2022-03", out)

    def test_no_observations_before_series_start(self):
        with mock.patch.object(
            consumer_inflation_expectations, "_request", side_effect=_stub()
        ):
            out = consumer_inflation_expectations.get_consumer_inflation_expectations(
                "2021-01-01"
            )
        self.assertIn("No", out)
        self.assertIn("2021-01-01", out)


@pytest.mark.unit
class SceFormatErrorTests(_SceTestCase):
    def _get(self, content):
        with mock.patch.object(
            consumer_inflation_expectations, "_request", side_effect=_stub(content)
        ):
            return consumer_inflation_expectations.get_consumer_inflation_expectations(
                "2022-05-31"
            )

    def test_html_error_page_errors_loudly(self):
        # The NY Fed site returns a 200 HTML error page for bad paths; that
        # must surface a clear error naming the source, never a false report.
        out = self._get(b"<html>Sitecore error page</html>")
        self.assertIn("ERROR", out)
        self.assertIn("New York Fed", out)
        self.assertNotIn("No SCE", out)

    def test_missing_five_year_sheet_errors_loudly(self):
        out = self._get(_build_xlsx(include_five_year_sheet=False))
        self.assertIn("ERROR", out)
        self.assertIn("New York Fed", out)

    def test_missing_median_column_errors_loudly(self):
        header = list(_INFL_HEADER)
        header[1] = "Median 1yr inflation"  # renamed column
        out = self._get(_build_xlsx(infl_header=header))
        self.assertIn("ERROR", out)
        self.assertIn("New York Fed", out)

    def test_bad_month_key_errors_loudly(self):
        rows = [list(r) for r in _INFL_ROWS]
        rows[0][0] = "Dec-2021"  # not an integer YYYYMM
        out = self._get(_build_xlsx(infl_rows=rows))
        self.assertIn("ERROR", out)
        self.assertIn("New York Fed", out)

    def test_non_numeric_value_errors_loudly(self):
        rows = [list(r) for r in _INFL_ROWS]
        rows[0][1] = "abc"
        out = self._get(_build_xlsx(infl_rows=rows))
        self.assertIn("ERROR", out)
        self.assertIn("New York Fed", out)

    def test_malformed_download_is_not_cached(self):
        self._get(b"<html>oops</html>")
        self.assertFalse(os.path.exists(self._cache_dir()))

    def test_network_error_propagates(self):
        with mock.patch.object(
            consumer_inflation_expectations,
            "_request",
            side_effect=requests.ConnectionError("boom"),
        ), self.assertRaises(requests.ConnectionError):
            consumer_inflation_expectations.get_consumer_inflation_expectations(
                "2022-05-31"
            )


@pytest.mark.unit
class SceCacheTests(_SceTestCase):
    def test_fresh_cache_is_reused(self):
        with mock.patch.object(
            consumer_inflation_expectations, "_request", side_effect=_stub()
        ) as m:
            consumer_inflation_expectations.get_consumer_inflation_expectations(
                "2022-05-31"
            )
            consumer_inflation_expectations.get_consumer_inflation_expectations(
                "2022-05-31"
            )
        self.assertEqual(m.call_count, 1)

    def test_cache_is_written_under_ny_fed_sce_dir(self):
        with mock.patch.object(
            consumer_inflation_expectations, "_request", side_effect=_stub()
        ):
            consumer_inflation_expectations.get_consumer_inflation_expectations(
                "2022-05-31"
            )
        files = os.listdir(self._cache_dir())
        self.assertEqual(len(files), 1)
        self.assertTrue(files[0].endswith(".xlsx"))

    def test_stale_cache_is_refetched(self):
        # The series updates monthly; cached files older than 30 days are
        # re-downloaded.
        with mock.patch.object(
            consumer_inflation_expectations, "_request", side_effect=_stub()
        ) as m:
            consumer_inflation_expectations.get_consumer_inflation_expectations(
                "2022-05-31"
            )
            path = os.path.join(self._cache_dir(), os.listdir(self._cache_dir())[0])
            stale = time.time() - 31 * 24 * 3600
            os.utime(path, (stale, stale))
            consumer_inflation_expectations.get_consumer_inflation_expectations(
                "2022-05-31"
            )
        self.assertEqual(m.call_count, 2)


if __name__ == "__main__":
    unittest.main()
