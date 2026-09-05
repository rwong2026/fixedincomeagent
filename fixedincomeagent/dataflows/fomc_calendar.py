"""FOMC meeting calendar and statement text (local files).

Reports the FOMC meetings bracketing ``curr_date`` — the most recent decision
and the next scheduled meeting — plus a reference to the stored statement
text for the recent meeting.

The meeting list is STATIC: the FOMC publishes its calendar years in advance,
so it is known ahead of time and carries no lookahead risk. It was verified
against the official calendars on 2026-09-05:

* 2021-2027: https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm
* 2019:      https://www.federalreserve.gov/monetarypolicy/fomchistorical2019.htm
* 2020:      https://www.federalreserve.gov/monetarypolicy/fomchistorical2020.htm

**Update annually**: extend the list each January when the Fed posts the next
year's calendar (currently published through 2027).

The plan's suggestion to supplement with FRED ``DFEDTARU`` for target-rate
decisions is deliberately skipped: rate decisions come from the fred.py
vendor when needed, and dropping the FRED call keeps this module
offline-deterministic (no API key, no network).

Two adjustments to the raw calendar, both visible on the 2020 page: the
March 17-18, 2020 meeting was CANCELLED and is excluded, and the two
unscheduled March 2020 emergency meetings (Mar 3 and Mar 15 decisions) are
included — they are historical fact for any backtest date after they
occurred, and the Mar 15 meeting cut the target range to 0-0.25%.

Statement text is ingested from LOCAL FILES ONLY (no scraping): save the
statement HTML/text for a meeting as
``data_cache_dir/fomc_statements/<decision-date>.txt`` where the decision
date is the LAST day of the meeting (the day the statement is released),
e.g. ``2024-06-12.txt``. A file is only referenced when its decision date is
on or before ``curr_date``, so historical runs never see future statements.
"""
import os
from dataclasses import dataclass
from datetime import date, datetime

from .config import get_config

# Characters of statement text quoted in the report; enough to convey the
# decision without flooding agent context.
STATEMENT_EXCERPT_CHARS = 300


@dataclass(frozen=True)
class Meeting:
    """An FOMC meeting. ``end`` is the decision day (statement release)."""

    start: date
    end: date
    sep: bool = False  # meeting with a Summary of Economic Projections (dot plot)
    note: str = ""


# (start, end, sep, note) — sorted by decision date. See module docstring for
# sources. "*" meetings on federalreserve.gov have projection materials.
_MEETING_ROWS = [
    # 2019 (fomchistorical2019.htm)
    ("2019-01-29", "2019-01-30", False, ""),
    ("2019-03-19", "2019-03-20", True, ""),
    ("2019-04-30", "2019-05-01", False, ""),
    ("2019-06-18", "2019-06-19", True, ""),
    ("2019-07-30", "2019-07-31", False, ""),
    ("2019-09-17", "2019-09-18", True, ""),
    ("2019-10-29", "2019-10-30", False, ""),
    ("2019-12-10", "2019-12-11", True, ""),
    # 2020 (fomchistorical2020.htm; Mar 17-18 meeting cancelled)
    ("2020-01-28", "2020-01-29", False, ""),
    ("2020-03-03", "2020-03-03", False,
     "unscheduled emergency meeting (held Mar 2, statement released Mar 3)"),
    ("2020-03-15", "2020-03-15", False,
     "unscheduled emergency meeting replacing the cancelled Mar 17-18 meeting"),
    ("2020-04-28", "2020-04-29", False, ""),
    ("2020-06-09", "2020-06-10", True, ""),
    ("2020-07-28", "2020-07-29", False, ""),
    ("2020-09-15", "2020-09-16", True, ""),
    ("2020-11-04", "2020-11-05", False, ""),
    ("2020-12-15", "2020-12-16", True, ""),
    # 2021
    ("2021-01-26", "2021-01-27", False, ""),
    ("2021-03-16", "2021-03-17", True, ""),
    ("2021-04-27", "2021-04-28", False, ""),
    ("2021-06-15", "2021-06-16", True, ""),
    ("2021-07-27", "2021-07-28", False, ""),
    ("2021-09-21", "2021-09-22", True, ""),
    ("2021-11-02", "2021-11-03", False, ""),
    ("2021-12-14", "2021-12-15", True, ""),
    # 2022
    ("2022-01-25", "2022-01-26", False, ""),
    ("2022-03-15", "2022-03-16", True, ""),
    ("2022-05-03", "2022-05-04", False, ""),
    ("2022-06-14", "2022-06-15", True, ""),
    ("2022-07-26", "2022-07-27", False, ""),
    ("2022-09-20", "2022-09-21", True, ""),
    ("2022-11-01", "2022-11-02", False, ""),
    ("2022-12-13", "2022-12-14", True, ""),
    # 2023
    ("2023-01-31", "2023-02-01", False, ""),
    ("2023-03-21", "2023-03-22", True, ""),
    ("2023-05-02", "2023-05-03", False, ""),
    ("2023-06-13", "2023-06-14", True, ""),
    ("2023-07-25", "2023-07-26", False, ""),
    ("2023-09-19", "2023-09-20", True, ""),
    ("2023-10-31", "2023-11-01", False, ""),
    ("2023-12-12", "2023-12-13", True, ""),
    # 2024
    ("2024-01-30", "2024-01-31", False, ""),
    ("2024-03-19", "2024-03-20", True, ""),
    ("2024-04-30", "2024-05-01", False, ""),
    ("2024-06-11", "2024-06-12", True, ""),
    ("2024-07-30", "2024-07-31", False, ""),
    ("2024-09-17", "2024-09-18", True, ""),
    ("2024-11-06", "2024-11-07", False, ""),
    ("2024-12-17", "2024-12-18", True, ""),
    # 2025
    ("2025-01-28", "2025-01-29", False, ""),
    ("2025-03-18", "2025-03-19", True, ""),
    ("2025-05-06", "2025-05-07", False, ""),
    ("2025-06-17", "2025-06-18", True, ""),
    ("2025-07-29", "2025-07-30", False, ""),
    ("2025-09-16", "2025-09-17", True, ""),
    ("2025-10-28", "2025-10-29", False, ""),
    ("2025-12-09", "2025-12-10", True, ""),
    # 2026
    ("2026-01-27", "2026-01-28", False, ""),
    ("2026-03-17", "2026-03-18", True, ""),
    ("2026-04-28", "2026-04-29", False, ""),
    ("2026-06-16", "2026-06-17", True, ""),
    ("2026-07-28", "2026-07-29", False, ""),
    ("2026-09-15", "2026-09-16", True, ""),
    ("2026-10-27", "2026-10-28", False, ""),
    ("2026-12-08", "2026-12-09", True, ""),
    # 2027
    ("2027-01-26", "2027-01-27", False, ""),
    ("2027-03-16", "2027-03-17", True, ""),
    ("2027-04-27", "2027-04-28", False, ""),
    ("2027-06-08", "2027-06-09", True, ""),
    ("2027-07-27", "2027-07-28", False, ""),
    ("2027-09-14", "2027-09-15", True, ""),
    ("2027-10-26", "2027-10-27", False, ""),
    ("2027-12-07", "2027-12-08", True, ""),
]

FOMC_MEETINGS = [
    Meeting(
        date.fromisoformat(start), date.fromisoformat(end), sep, note
    )
    for start, end, sep, note in _MEETING_ROWS
]


def _statement_path(decision: date) -> str:
    return os.path.join(
        get_config()["data_cache_dir"], "fomc_statements", f"{decision}.txt"
    )


def _fmt_meeting(m: Meeting) -> str:
    label = f"{m.start} to {m.end}" if m.start != m.end else f"{m.start}"
    extras = []
    if m.sep:
        extras.append("SEP/dot-plot meeting")
    if m.note:
        extras.append(m.note)
    return label + (f" ({'; '.join(extras)})" if extras else "")


def get_fomc_calendar(curr_date: str) -> str:
    """Report the FOMC meetings bracketing ``curr_date`` as markdown.

    Args:
        curr_date: The as-of date (yyyy-mm-dd). Meetings are reported
            relative to it with no lookahead: the most recent meeting is the
            latest whose decision day is on or before ``curr_date``, and
            statement text is referenced only for such meetings.

    Returns:
        A markdown report with the most recent meeting (with SEP flag and a
        statement-text reference or absence note) and the next scheduled
        meeting.
    """
    as_of = datetime.strptime(curr_date, "%Y-%m-%d").date()
    past = [m for m in FOMC_MEETINGS if m.end <= as_of]
    future = [m for m in FOMC_MEETINGS if m.end > as_of]

    header = (
        "## FOMC Calendar\n"
        "- Source: static meeting list verified against federalreserve.gov "
        "(see module docstring); update annually\n"
        f"- As of: {as_of}\n"
    )

    sections = []
    if past:
        recent = past[-1]
        section = f"\n**Most recent meeting:** {_fmt_meeting(recent)}\n"
        path = _statement_path(recent.end)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                excerpt = " ".join(f.read().split())[:STATEMENT_EXCERPT_CHARS]
            section += f'\nStatement ({path}):\n\n> "{excerpt}..."\n'
        else:
            section += (
                f"\nNo statement text on file for {recent.end}. To add it, "
                f"save the statement from federalreserve.gov to {path}.\n"
            )
        sections.append(section)

    if future:
        nxt = future[0]
        status = "in progress" if nxt.start <= as_of else f"in {(nxt.start - as_of).days} days"
        sections.append(f"\n**Next meeting:** {_fmt_meeting(nxt)} ({status})\n")

    return header + "".join(sections)
