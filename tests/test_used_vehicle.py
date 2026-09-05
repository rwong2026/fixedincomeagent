"""Manheim Used Vehicle Value Index — manual local-CSV ingest.

The module reads ``data_cache_dir/manheim/used_vehicle_index.csv`` (a
manually maintained file; there is no free Manheim feed). These tests run
fully offline against fixture CSVs written to a temp ``data_cache_dir``.

The fixture covers 2025-01 .. 2026-08 (20 month-end rows): 200.0 for every
2025 month and 210.0 for every 2026 month, so YoY for any 2026 month is
210/200 - 1 = +5.0% and 2025 months have no prior-year counterpart (blank
YoY).
"""
import calendar
import copy
import os
import tempfile
import unittest

import pytest

import fixedincomeagent.dataflows.config as config_module
import fixedincomeagent.default_config as default_config
from fixedincomeagent.dataflows import used_vehicle_index
from fixedincomeagent.dataflows.config import set_config


def _month_ends():
    y, m = 2025, 1
    while (y, m) <= (2026, 8):
        yield y, m
        m += 1
        if m == 13:
            y, m = y + 1, 1


_FIXTURE = (
    "date,index_value\n"
    + "\n".join(
        f"{y}-{m:02d}-{calendar.monthrange(y, m)[1]:02d},"
        f"{200.0 if y == 2025 else 210.0}"
        for y, m in _month_ends()
    )
    + "\n"
)


class _UsedVehicleTestCase(unittest.TestCase):
    """Redirect the data cache to a temp dir so tests never touch the real one."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        set_config({"data_cache_dir": self._tmp})

    def tearDown(self):
        config_module._config = copy.deepcopy(default_config.DEFAULT_CONFIG)

    def _write_csv(self, text=_FIXTURE):
        d = os.path.join(self._tmp, "manheim")
        os.makedirs(d)
        path = os.path.join(d, "used_vehicle_index.csv")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path


@pytest.mark.unit
class UsedVehicleReportTests(_UsedVehicleTestCase):
    def test_report_structure_and_latest_values(self):
        self._write_csv()
        out = used_vehicle_index.get_used_vehicle_index("2026-09-05")
        self.assertIn("## Manheim Used Vehicle Index", out)
        self.assertIn("As-of date: 2026-09-05", out)
        self.assertIn("manually maintained", out)
        self.assertIn("| Month | Index | YoY |", out)
        self.assertIn("| 2026-08 | 210.0 | +5.0% |", out)

    def test_blank_yoy_when_no_prior_year_month(self):
        self._write_csv()
        out = used_vehicle_index.get_used_vehicle_index("2026-09-05")
        self.assertIn("| 2025-10 | 200.0 |  |", out)

    def test_curr_date_excludes_future_months(self):
        self._write_csv()
        out = used_vehicle_index.get_used_vehicle_index("2026-06-15")
        self.assertIn("| 2026-05 | 210.0 | +5.0% |", out)
        self.assertNotIn("| 2026-06 |", out)
        self.assertNotIn("| 2026-08 |", out)

    def test_month_cap_note(self):
        self._write_csv()
        out = used_vehicle_index.get_used_vehicle_index("2026-09-05")
        self.assertIn("showing the most recent 12 of 20 months", out)
        self.assertNotIn("2025-01", out)

    def test_no_observations_before_series_start(self):
        self._write_csv()
        out = used_vehicle_index.get_used_vehicle_index("2020-01-01")
        self.assertIn("No Manheim index observations on or before 2020-01-01", out)


@pytest.mark.unit
class UsedVehicleIngestTests(_UsedVehicleTestCase):
    def test_absent_file_is_graceful_report(self):
        out = used_vehicle_index.get_used_vehicle_index("2026-09-05")
        self.assertNotIn("ERROR", out)
        self.assertIn("## Manheim Used Vehicle Index", out)
        self.assertIn("not available", out)
        self.assertIn("manually maintained", out)

    def test_malformed_csv_errors_loudly(self):
        self._write_csv("not,a,valid\n1,2,3\n")
        out = used_vehicle_index.get_used_vehicle_index("2026-09-05")
        self.assertIn("ERROR", out)
        self.assertIn("Manheim", out)

    def test_bad_date_errors_loudly(self):
        self._write_csv("date,index_value\nnot-a-date,210.0\n")
        out = used_vehicle_index.get_used_vehicle_index("2026-09-05")
        self.assertIn("ERROR", out)
        self.assertIn("Manheim", out)

    def test_non_numeric_value_errors_loudly(self):
        self._write_csv("date,index_value\n2026-08-31,abc\n")
        out = used_vehicle_index.get_used_vehicle_index("2026-09-05")
        self.assertIn("ERROR", out)
        self.assertIn("Manheim", out)

    def test_empty_csv_errors_loudly(self):
        self._write_csv("date,index_value\n")
        out = used_vehicle_index.get_used_vehicle_index("2026-09-05")
        self.assertIn("ERROR", out)
        self.assertIn("Manheim", out)


if __name__ == "__main__":
    unittest.main()
