"""ISM Manufacturing Prices Index ("prices paid") — manual local-CSV ingest.

The module reads ``data_cache_dir/ism/prices_paid.csv`` (a manually
maintained file; ISM history is paywalled, so tracking is forward-only).
These tests run fully offline against fixture CSVs written to a temp
``data_cache_dir``.

The fixture covers 2025-07 .. 2026-08 (14 month-end rows), rising exactly
1.0 point per month from 55.0, so every month after the first has a MoM
change of +1.0 and the first month has none (blank).
"""
import calendar
import copy
import os
import tempfile
import unittest

import pytest

import fixedincomeagent.dataflows.config as config_module
import fixedincomeagent.default_config as default_config
from fixedincomeagent.dataflows import ism_prices_paid
from fixedincomeagent.dataflows.config import set_config


def _month_ends():
    y, m = 2025, 7
    while (y, m) <= (2026, 8):
        yield y, m
        m += 1
        if m == 13:
            y, m = y + 1, 1


_FIXTURE = (
    "date,prices_index\n"
    + "\n".join(
        f"{y}-{m:02d}-{calendar.monthrange(y, m)[1]:02d},{55.0 + i:.1f}"
        for i, (y, m) in enumerate(_month_ends())
    )
    + "\n"
)


class _IsmTestCase(unittest.TestCase):
    """Redirect the data cache to a temp dir so tests never touch the real one."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        set_config({"data_cache_dir": self._tmp})

    def tearDown(self):
        config_module._config = copy.deepcopy(default_config.DEFAULT_CONFIG)

    def _write_csv(self, text=_FIXTURE):
        d = os.path.join(self._tmp, "ism")
        os.makedirs(d)
        path = os.path.join(d, "prices_paid.csv")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path


@pytest.mark.unit
class IsmReportTests(_IsmTestCase):
    def test_report_structure_and_latest_values(self):
        self._write_csv()
        out = ism_prices_paid.get_ism_prices_paid("2026-09-05")
        self.assertIn("## ISM Prices Paid", out)
        self.assertIn("As-of date: 2026-09-05", out)
        self.assertIn("forward-only", out)
        self.assertIn("| Month | Prices Index | MoM |", out)
        self.assertIn("| 2026-08 | 68.0 | +1.0 |", out)

    def test_first_month_has_blank_mom(self):
        self._write_csv()
        out = ism_prices_paid.get_ism_prices_paid("2025-08-15")
        self.assertIn("| 2025-07 | 55.0 |  |", out)

    def test_curr_date_excludes_future_months(self):
        self._write_csv()
        out = ism_prices_paid.get_ism_prices_paid("2026-04-10")
        self.assertIn("| 2026-03 | 63.0 | +1.0 |", out)
        self.assertNotIn("| 2026-04 |", out)
        self.assertNotIn("| 2026-08 |", out)

    def test_month_cap_note(self):
        self._write_csv()
        out = ism_prices_paid.get_ism_prices_paid("2026-09-05")
        self.assertIn("showing the most recent 12 of 14 months", out)
        self.assertNotIn("| 2025-07 |", out)

    def test_no_observations_before_series_start(self):
        self._write_csv()
        out = ism_prices_paid.get_ism_prices_paid("2020-01-01")
        self.assertIn("No ISM prices paid observations on or before 2020-01-01", out)


@pytest.mark.unit
class IsmIngestTests(_IsmTestCase):
    def test_absent_file_is_graceful_report(self):
        out = ism_prices_paid.get_ism_prices_paid("2026-09-05")
        self.assertNotIn("ERROR", out)
        self.assertIn("## ISM Prices Paid", out)
        self.assertIn("not available", out)
        self.assertIn("manually maintained", out)

    def test_malformed_csv_errors_loudly(self):
        self._write_csv("not,a,valid\n1,2,3\n")
        out = ism_prices_paid.get_ism_prices_paid("2026-09-05")
        self.assertIn("ERROR", out)
        self.assertIn("ISM", out)

    def test_bad_date_errors_loudly(self):
        self._write_csv("date,prices_index\nnot-a-date,68.0\n")
        out = ism_prices_paid.get_ism_prices_paid("2026-09-05")
        self.assertIn("ERROR", out)
        self.assertIn("ISM", out)

    def test_non_numeric_value_errors_loudly(self):
        self._write_csv("date,prices_index\n2026-08-31,abc\n")
        out = ism_prices_paid.get_ism_prices_paid("2026-09-05")
        self.assertIn("ERROR", out)
        self.assertIn("ISM", out)

    def test_empty_csv_errors_loudly(self):
        self._write_csv("date,prices_index\n")
        out = ism_prices_paid.get_ism_prices_paid("2026-09-05")
        self.assertIn("ERROR", out)
        self.assertIn("ISM", out)


if __name__ == "__main__":
    unittest.main()
