"""Shelter & rents vendor (Zillow ZORI + Apartment List rent estimates).

All HTTP is mocked at the module's ``_request`` boundary, so these run with no
network connection. Caching and the Apartment List local-file ingest are
exercised against a temp ``data_cache_dir``.

The fixtures mirror the verified 2026-09-05 shapes: Zillow's national ZORI
file is a 2-line wide CSV (one row, month-end date columns); the fixture adds
a second region row to prove the parser selects the United States row. The
Apartment List file is a quoted wide CSV keyed by (location_name, bed_size)
with ``YYYY_MM`` month columns; distractor rows (1br/2br/metro) hold 5555.
"""
import calendar
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
from fixedincomeagent.dataflows import shelter_rents
from fixedincomeagent.dataflows.config import set_config


def _month_seq(start_year, start_month, count):
    """Yield (year, month) for ``count`` consecutive months."""
    y, m = start_year, start_month
    for _ in range(count):
        yield y, m
        m += 1
        if m == 13:
            y, m = y + 1, 1


# Zillow ZORI fixture: 2024-08 .. 2026-07 (24 months). Flat 1800 through
# 2025-07, then +8/month, so YoY(2026-07) = 1896/1800 - 1 = +5.3% and
# YoY(2026-06) = 1888/1800 - 1 = +4.9%.
_ZORI_MONTHS = list(_month_seq(2024, 8, 24))
_ZORI_VALUES = [1800 + max(0, i - 11) * 8 for i in range(24)]


def _zillow_csv():
    cols = [
        f"{y}-{m:02d}-{calendar.monthrange(y, m)[1]:02d}" for y, m in _ZORI_MONTHS
    ]
    header = "RegionID,SizeRank,RegionName,RegionType," + ",".join(cols)
    us = "102001,0,United States,country," + ",".join(str(v) for v in _ZORI_VALUES)
    metro = "34999,1,Some Metro,msa," + ",".join("5555" for _ in cols)
    return "\n".join([header, us, metro]) + "\n"


# Apartment List fixture: 2024_08 .. 2026_06 (23 months). Flat 1300 through
# 2025_06, then -1/month, so YoY(2026_06) = 1288/1300 - 1 = -0.9%.
_AL_MONTHS = list(_month_seq(2024, 8, 23))
_AL_VALUES = [1300 - max(0, i - 10) for i in range(23)]


def _apartment_list_csv():
    cols = [f"{y}_{m:02d}" for y, m in _AL_MONTHS]
    header = (
        '"location_name","location_type","location_fips_code","population",'
        '"state","county","metro","bed_size",' + ",".join(f'"{c}"' for c in cols)
    )

    def row(name, loc_type, bed_size, values):
        return (
            f'"{name}","{loc_type}",0,331097593,,,,"{bed_size}",'
            + ",".join(str(v) for v in values)
        )

    junk = ["5555"] * len(cols)
    return "\n".join(
        [
            header,
            row("United States", "National", "overall", _AL_VALUES),
            row("United States", "National", "1br", junk),
            row("United States", "National", "2br", junk),
            row("Akron, OH", "Metro", "overall", junk),
        ]
    ) + "\n"


def _stub(text=None, captured=None):
    body = _zillow_csv() if text is None else text

    def _impl(url, params=None):
        if captured is not None:
            captured.append(url)
        return body

    return _impl


class _ShelterTestCase(unittest.TestCase):
    """Redirect the data cache to a temp dir so tests never touch the real one."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        set_config({"data_cache_dir": self._tmp})

    def tearDown(self):
        config_module._config = copy.deepcopy(default_config.DEFAULT_CONFIG)

    def _zillow_cache_dir(self):
        return os.path.join(self._tmp, "zillow")

    def _write_apartment_list(self, text=None):
        d = os.path.join(self._tmp, "apartment_list")
        os.makedirs(d)
        path = os.path.join(d, "Apartment_List_Rent_Estimates_2026_06.csv")
        with open(path, "w", encoding="utf-8") as f:
            f.write(_apartment_list_csv() if text is None else text)
        return path


@pytest.mark.unit
class ShelterReportTests(_ShelterTestCase):
    def test_report_structure_and_latest_values(self):
        self._write_apartment_list()
        with mock.patch.object(shelter_rents, "_request", side_effect=_stub()):
            out = shelter_rents.get_shelter_rents("2026-09-05")
        self.assertIn("## Shelter & Rents", out)
        self.assertIn("Zillow ZORI", out)
        self.assertIn("Apartment List", out)
        self.assertIn("As-of date: 2026-09-05", out)
        # Latest readings table: both sources, YoY vs 12 months earlier.
        self.assertIn("| Zillow ZORI | 2026-07 | $1,896 | +5.3% |", out)
        self.assertIn("| Apartment List | 2026-06 | $1,288 | -0.9% |", out)

    def test_monthly_table_compares_both_sources(self):
        self._write_apartment_list()
        with mock.patch.object(shelter_rents, "_request", side_effect=_stub()):
            out = shelter_rents.get_shelter_rents("2026-09-05")
        # A month covered by both sources shows both levels + YoYs.
        self.assertIn("| 2026-06 | $1,888 | +4.9% | $1,288 | -0.9% |", out)
        # A month only Zillow has (AL file ends 2026_06) shows empty AL cells.
        self.assertIn("| 2026-07 | $1,896 | +5.3% |  |  |", out)
        # Distractor rows (1br/2br/metro, all 5555) must never leak.
        self.assertNotIn("5555", out)

    def test_curr_date_excludes_future_months(self):
        self._write_apartment_list()
        with mock.patch.object(shelter_rents, "_request", side_effect=_stub()):
            out = shelter_rents.get_shelter_rents("2026-06-15")
        # 2026-06-30/2026-07-31 (ZORI) and 2026_06 (Apartment List) month-ends
        # are all after the as-of date.
        self.assertNotIn("$1,896", out)
        self.assertNotIn("$1,888", out)
        self.assertNotIn("$1,288", out)
        self.assertIn("| Zillow ZORI | 2026-05 | $1,880 |", out)
        self.assertIn("| Apartment List | 2026-05 | $1,289 |", out)

    def test_month_cap_note(self):
        self._write_apartment_list()
        with mock.patch.object(shelter_rents, "_request", side_effect=_stub()):
            out = shelter_rents.get_shelter_rents("2026-09-05")
        # 24 Zillow months span 2024-08..2026-07; the table caps at 12.
        self.assertIn("showing the most recent 12 of 24 months", out)
        self.assertNotIn("2024-08", out)

    def test_no_observations_before_series_start(self):
        with mock.patch.object(shelter_rents, "_request", side_effect=_stub()):
            out = shelter_rents.get_shelter_rents("2020-01-01")
        self.assertIn("No rent observations", out)
        self.assertIn("2020-01-01", out)


@pytest.mark.unit
class ApartmentListIngestTests(_ShelterTestCase):
    def test_missing_file_is_graceful_not_an_error(self):
        # No apartment_list directory at all: the Zillow leg still renders.
        with mock.patch.object(shelter_rents, "_request", side_effect=_stub()):
            out = shelter_rents.get_shelter_rents("2026-09-05")
        self.assertNotIn("ERROR", out)
        self.assertIn("not available", out)
        self.assertIn("| Zillow ZORI | 2026-07 | $1,896 | +5.3% |", out)
        self.assertNotIn("AptList $", out)

    def test_empty_directory_is_graceful(self):
        os.makedirs(os.path.join(self._tmp, "apartment_list"))
        with mock.patch.object(shelter_rents, "_request", side_effect=_stub()):
            out = shelter_rents.get_shelter_rents("2026-09-05")
        self.assertNotIn("ERROR", out)
        self.assertIn("not available", out)

    def test_malformed_local_file_errors_loudly(self):
        self._write_apartment_list("not,a,valid\n1,2,3\n")
        with mock.patch.object(shelter_rents, "_request", side_effect=_stub()):
            out = shelter_rents.get_shelter_rents("2026-09-05")
        self.assertIn("ERROR", out)
        self.assertIn("Apartment List", out)

    def test_missing_overall_row_errors_loudly(self):
        cols = [f"{y}_{m:02d}" for y, m in _AL_MONTHS]
        header = (
            '"location_name","location_type","location_fips_code","population",'
            '"state","county","metro","bed_size",'
            + ",".join(f'"{c}"' for c in cols)
        )
        only_1br = header + '\n"United States","National",0,331097593,,,,"1br",' + ",".join(
            "5555" for _ in cols
        )
        self._write_apartment_list(only_1br)
        with mock.patch.object(shelter_rents, "_request", side_effect=_stub()):
            out = shelter_rents.get_shelter_rents("2026-09-05")
        self.assertIn("ERROR", out)
        self.assertIn("Apartment List", out)


@pytest.mark.unit
class ZillowFormatErrorTests(_ShelterTestCase):
    def test_html_error_page_errors_loudly(self):
        # A 200 with a changed body must surface a clear error naming the
        # source — never a false "no data" report.
        stub = _stub("<html>nginx error page</html>")
        with mock.patch.object(shelter_rents, "_request", side_effect=stub):
            out = shelter_rents.get_shelter_rents("2026-09-05")
        self.assertIn("ERROR", out)
        self.assertIn("Zillow", out)
        # The diagnostic must echo the received body, not a literal
        # "{str(rows[0][:5])[:120]!r}" placeholder.
        self.assertIn("nginx error page", out)
        self.assertNotIn("{str(rows[0]", out)

    def test_missing_united_states_row_errors_loudly(self):
        cols = [
            f"{y}-{m:02d}-{calendar.monthrange(y, m)[1]:02d}"
            for y, m in _ZORI_MONTHS
        ]
        text = "RegionID,SizeRank,RegionName,RegionType," + ",".join(cols) + "\n"
        text += "34999,1,Some Metro,msa," + ",".join("5555" for _ in cols) + "\n"
        with mock.patch.object(shelter_rents, "_request", side_effect=_stub(text)):
            out = shelter_rents.get_shelter_rents("2026-09-05")
        self.assertIn("ERROR", out)
        self.assertIn("Zillow", out)

    def test_bad_date_columns_error_loudly(self):
        text = "RegionID,SizeRank,RegionName,RegionType,foo,bar\n"
        text += "102001,0,United States,country,1,2\n"
        with mock.patch.object(shelter_rents, "_request", side_effect=_stub(text)):
            out = shelter_rents.get_shelter_rents("2026-09-05")
        self.assertIn("ERROR", out)
        self.assertIn("Zillow", out)

    def test_malformed_download_is_not_cached(self):
        with mock.patch.object(
            shelter_rents, "_request", side_effect=_stub("<html>oops</html>")
        ):
            shelter_rents.get_shelter_rents("2026-09-05")
        self.assertFalse(os.path.exists(self._zillow_cache_dir()))

    def test_network_error_propagates(self):
        with mock.patch.object(
            shelter_rents, "_request",
            side_effect=requests.ConnectionError("boom"),
        ), self.assertRaises(requests.ConnectionError):
            shelter_rents.get_shelter_rents("2026-09-05")


@pytest.mark.unit
class ZillowCacheTests(_ShelterTestCase):
    def test_fresh_cache_is_reused(self):
        with mock.patch.object(
            shelter_rents, "_request", side_effect=_stub()
        ) as m:
            shelter_rents.get_shelter_rents("2026-09-05")
            shelter_rents.get_shelter_rents("2026-09-05")
        self.assertEqual(m.call_count, 1)

    def test_cache_is_written_under_zillow_dir(self):
        with mock.patch.object(shelter_rents, "_request", side_effect=_stub()):
            shelter_rents.get_shelter_rents("2026-09-05")
        files = os.listdir(self._zillow_cache_dir())
        self.assertEqual(len(files), 1)

    def test_stale_cache_is_refetched(self):
        with mock.patch.object(
            shelter_rents, "_request", side_effect=_stub()
        ) as m:
            shelter_rents.get_shelter_rents("2026-09-05")
            # Age the cache file past the 7-day TTL.
            path = os.path.join(
                self._zillow_cache_dir(), os.listdir(self._zillow_cache_dir())[0]
            )
            stale = time.time() - 8 * 24 * 3600
            os.utime(path, (stale, stale))
            shelter_rents.get_shelter_rents("2026-09-05")
        self.assertEqual(m.call_count, 2)


if __name__ == "__main__":
    unittest.main()
