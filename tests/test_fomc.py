"""FOMC calendar and Fed speeches vendors.

All HTTP is mocked at the modules' ``_request`` boundary, so these run with no
network connection. Statement-text storage is exercised against a temp
``data_cache_dir``.
"""
import copy
import os
import tempfile
import unittest
from unittest import mock

import pytest
import requests

import fixedincomeagent.dataflows.config as config_module
import fixedincomeagent.default_config as default_config
from fixedincomeagent.dataflows import fed_speeches, fomc_calendar
from fixedincomeagent.dataflows.config import set_config

# Fixture payload matching the verified shape of
# https://www.federalreserve.gov/feeds/speeches.xml (fetched 2026-09-05):
# RSS 2.0, channel/item, title is "Speaker, Title", pubDate is RFC 822.
_RSS = """<?xml version="1.0" encoding="utf-8" ?>
<rss version="2.0">
    <channel>
        <title>FRB: Speeches</title>
        <link><![CDATA[https://www.federalreserve.gov/feeds/feeds.htm]]></link>
        <description><![CDATA[Speeches of Federal Reserve Officials]]></description>
        <language>en</language>
        <item>
            <title>Waller, The Economic Outlook and Some Comments on My Policy Communication</title>
            <link><![CDATA[https://www.federalreserve.gov/newsevents/speech/waller20260903a.htm]]></link>
            <guid><![CDATA[https://www.federalreserve.gov/newsevents/speech/waller20260903a.htm]]></guid>
            <description><![CDATA[Speech At Reuters NEXT Newsmaker Interview, Washington, D.C.]]></description>
            <category>Speech</category>
            <pubDate><![CDATA[Thu, 3 Sep 2026 12:30:00 GMT]]></pubDate>
        </item>
        <item>
            <title>Warsh, In Our Time</title>
            <link><![CDATA[https://www.federalreserve.gov/newsevents/speech/warsh20260828a.htm]]></link>
            <guid><![CDATA[https://www.federalreserve.gov/newsevents/speech/warsh20260828a.htm]]></guid>
            <description><![CDATA[Speech At the Kansas City Fed Jackson Hole symposium]]></description>
            <category>Speech</category>
            <pubDate><![CDATA[Fri, 28 Aug 2026 14:00:00 GMT]]></pubDate>
        </item>
        <item>
            <title>Cook, Outlook for the U.S. and Alaskan Economies</title>
            <link><![CDATA[https://www.federalreserve.gov/newsevents/speech/cook20260805a.htm]]></link>
            <guid><![CDATA[https://www.federalreserve.gov/newsevents/speech/cook20260805a.htm]]></guid>
            <description><![CDATA[Speech At the Anchorage Economic Development Corporation]]></description>
            <category>Speech</category>
            <pubDate><![CDATA[Wed, 5 Aug 2026 20:05:00 GMT]]></pubDate>
        </item>
        <item>
            <title>Future, A Speech Dated After Curr Date</title>
            <link><![CDATA[https://www.federalreserve.gov/newsevents/speech/future20260910a.htm]]></link>
            <guid><![CDATA[https://www.federalreserve.gov/newsevents/speech/future20260910a.htm]]></guid>
            <description><![CDATA[Speech At a venue]]></description>
            <category>Speech</category>
            <pubDate><![CDATA[Thu, 10 Sep 2026 15:00:00 GMT]]></pubDate>
        </item>
    </channel>
</rss>
"""


class _FomcTestCase(unittest.TestCase):
    """Redirect the data cache to a temp dir so tests never touch the real one."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        set_config({"data_cache_dir": self._tmp})

    def tearDown(self):
        config_module._config = copy.deepcopy(default_config.DEFAULT_CONFIG)

    def _write_statement(self, decision_date: str, text: str = "The Committee seeks...") -> str:
        d = os.path.join(self._tmp, "fomc_statements")
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, f"{decision_date}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path


@pytest.mark.unit
class FomcDateListIntegrityTests(unittest.TestCase):
    def test_meetings_sorted_by_decision_date(self):
        decisions = [m.end for m in fomc_calendar.FOMC_MEETINGS]
        self.assertEqual(decisions, sorted(decisions))

    def test_eight_scheduled_meetings_per_regular_year(self):
        # 2019 and 2021-2027 are regular 8-meeting years; 2020 is special
        # (7 scheduled after the March cancellation + 2 emergency meetings).
        for year in [2019] + list(range(2021, 2028)):
            count = sum(1 for m in fomc_calendar.FOMC_MEETINGS if m.start.year == year)
            self.assertEqual(count, 8, f"year {year}")
        self.assertEqual(
            sum(1 for m in fomc_calendar.FOMC_MEETINGS if m.start.year == 2020), 9
        )

    def test_four_sep_meetings_per_regular_year(self):
        for year in [2019] + list(range(2021, 2028)):
            seps = sum(
                1 for m in fomc_calendar.FOMC_MEETINGS if m.start.year == year and m.sep
            )
            self.assertEqual(seps, 4, f"year {year}")

    def test_covers_backtest_years_2019_through_2027(self):
        years = {m.start.year for m in fomc_calendar.FOMC_MEETINGS}
        self.assertTrue({2019, 2020, 2022, 2024, 2025}.issubset(years))
        self.assertIn(2027, years)


@pytest.mark.unit
class FomcCalendarTests(_FomcTestCase):
    def test_returns_markdown(self):
        result = fomc_calendar.get_fomc_calendar("2024-06-15")
        self.assertIsInstance(result, str)
        self.assertIn("## FOMC", result)

    def test_next_and_recent_meeting_around_curr_date(self):
        out = fomc_calendar.get_fomc_calendar("2024-06-15")
        # June 11-12, 2024 was a SEP meeting with decision day 2024-06-12.
        self.assertIn("2024-06-12", out)
        self.assertIn("Most recent", out)
        # Next scheduled meeting was July 30-31, 2024.
        self.assertIn("2024-07-31", out)
        self.assertIn("Next", out)

    def test_sep_meeting_is_flagged(self):
        out = fomc_calendar.get_fomc_calendar("2024-06-15")
        self.assertIn("SEP", out)

    def test_decision_day_itself_counts_as_most_recent(self):
        out = fomc_calendar.get_fomc_calendar("2024-06-12")
        self.assertIn("Most recent", out)
        self.assertIn("2024-06-12", out)
        # the June meeting is now past, so next must be July
        self.assertIn("2024-07-31", out)

    def test_before_first_meeting_has_no_recent(self):
        out = fomc_calendar.get_fomc_calendar("2018-06-15")
        self.assertIn("Next", out)
        self.assertIn("2019-01-30", out)
        self.assertNotIn("Most recent meeting:", out)

    def test_after_last_meeting_has_no_next(self):
        out = fomc_calendar.get_fomc_calendar("2028-06-15")
        self.assertIn("Most recent", out)
        self.assertIn("2027-12-08", out)
        self.assertNotIn("Next meeting:", out)

    def test_emergency_march_2020_meetings_are_recent_for_late_march(self):
        # The March 17-18, 2020 meeting was cancelled and replaced by the
        # unscheduled March 15 meeting (cut to zero); an emergency cut on
        # March 3 also occurred. A late-March 2020 run must see March 15 as
        # the most recent decision, not the cancelled scheduled meeting.
        out = fomc_calendar.get_fomc_calendar("2020-03-20")
        self.assertIn("2020-03-15", out)
        self.assertNotIn("2020-03-17", out)
        self.assertNotIn("2020-03-18", out)

    def test_statement_file_present_is_referenced_with_excerpt(self):
        self._write_statement("2024-06-12", "The Committee decided to maintain the target range.")
        out = fomc_calendar.get_fomc_calendar("2024-06-15")
        self.assertIn("2024-06-12.txt", out)
        self.assertIn("maintain the target range", out)

    def test_statement_file_absent_is_noted(self):
        out = fomc_calendar.get_fomc_calendar("2024-06-15")
        self.assertIn("No statement text", out)
        self.assertIn("fomc_statements", out)

    def test_statement_file_for_future_meeting_is_not_referenced(self):
        # Point-in-time: a file for the NEXT meeting (2024-07-31) must not
        # leak into a 2024-06-15 run, even if it exists on disk.
        self._write_statement("2024-07-31", "future statement text")
        out = fomc_calendar.get_fomc_calendar("2024-06-15")
        self.assertNotIn("future statement text", out)


@pytest.mark.unit
class FedSpeechesTests(_FomcTestCase):
    def test_returns_markdown(self):
        with mock.patch.object(fed_speeches, "_request", return_value=_RSS):
            result = fed_speeches.get_fed_speeches("2026-09-05")
        self.assertIsInstance(result, str)
        self.assertIn("## ", result)
        self.assertIn("Speeches", result)

    def test_parses_speaker_title_link_and_date(self):
        with mock.patch.object(fed_speeches, "_request", return_value=_RSS):
            out = fed_speeches.get_fed_speeches("2026-09-05")
        self.assertIn("Waller", out)
        self.assertIn("The Economic Outlook", out)
        self.assertIn("2026-09-03", out)
        self.assertIn(
            "https://www.federalreserve.gov/newsevents/speech/waller20260903a.htm", out
        )
        # the description/summary (venue) is parsed into the Venue column
        self.assertIn("Reuters NEXT Newsmaker Interview", out)

    def test_look_back_window_filters_old_items(self):
        # Cook's 2026-08-05 speech is 31 days back, outside the default 14.
        with mock.patch.object(fed_speeches, "_request", return_value=_RSS):
            out = fed_speeches.get_fed_speeches("2026-09-05")
        self.assertNotIn("Alaskan", out)
        # ... but included with a longer window
        with mock.patch.object(fed_speeches, "_request", return_value=_RSS):
            out = fed_speeches.get_fed_speeches("2026-09-05", look_back_days=40)
        self.assertIn("Alaskan", out)

    def test_items_after_curr_date_are_excluded(self):
        # Point-in-time: the 2026-09-10 speech is in the feed but after
        # curr_date and must not leak into a 2026-09-05 run.
        with mock.patch.object(fed_speeches, "_request", return_value=_RSS):
            out = fed_speeches.get_fed_speeches("2026-09-05", look_back_days=40)
        self.assertNotIn("Future", out)
        self.assertNotIn("future20260910a", out)

    def test_report_shows_window(self):
        with mock.patch.object(fed_speeches, "_request", return_value=_RSS):
            out = fed_speeches.get_fed_speeches("2026-09-05")
        self.assertIn("Window: 2026-08-22 to 2026-09-05", out)

    def test_empty_window_reports_no_speeches(self):
        with mock.patch.object(fed_speeches, "_request", return_value=_RSS):
            out = fed_speeches.get_fed_speeches("2026-01-15")
        self.assertIn("No Fed speeches", out)

    def test_rss_unavailable_falls_back_to_manual_note(self):
        with mock.patch.object(
            fed_speeches, "_request", side_effect=requests.ConnectionError("down")
        ):
            out = fed_speeches.get_fed_speeches("2026-09-05")
        self.assertIn("## ", out)
        self.assertIn("unavailable", out.lower())
        # fallback flags for manual update with the human speeches page
        self.assertIn("manual", out.lower())
        self.assertIn("newsevents/speeches", out)

    def test_malformed_xml_falls_back_to_manual_note(self):
        with mock.patch.object(fed_speeches, "_request", return_value="<html>oops"):
            out = fed_speeches.get_fed_speeches("2026-09-05")
        self.assertIn("unavailable", out.lower())
        self.assertIn("manual", out.lower())

    def test_malformed_pubdate_falls_back_to_manual_note(self):
        # Regression: an unparseable pubDate raised a bare ValueError out of
        # get_fed_speeches, killing the report run. A pubDate format change is
        # a shape change and must hit the loud fallback instead.
        bad = _RSS.replace(
            "Thu, 3 Sep 2026 12:30:00 GMT", "not-a-date"
        )
        with mock.patch.object(fed_speeches, "_request", return_value=bad):
            out = fed_speeches.get_fed_speeches("2026-09-05")
        self.assertIn("unavailable", out.lower())
        self.assertIn("manual", out.lower())
        self.assertIn("pubDate", out)

    def test_table_structure(self):
        with mock.patch.object(fed_speeches, "_request", return_value=_RSS):
            out = fed_speeches.get_fed_speeches("2026-09-05")
        self.assertIn("| Date | Speaker | Title |", out)
        # most recent first
        self.assertLess(out.index("2026-09-03"), out.index("2026-08-28"))


if __name__ == "__main__":
    unittest.main()
