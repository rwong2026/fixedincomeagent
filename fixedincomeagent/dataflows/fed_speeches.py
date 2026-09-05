"""Fed speeches vendor: recent speeches by Federal Reserve officials.

Source: the Board's public RSS feed at
``https://www.federalreserve.gov/feeds/speeches.xml`` (verified 2026-09-05:
RSS 2.0, ``channel/item`` entries; item ``title`` is ``"Speaker, Title"``,
``pubDate`` is RFC 822 GMT). The feed only carries the most recent ~15
speeches, so it is a live source: historical (backtest) runs far in the past
will usually find no in-window items, which the report states plainly.

If the feed is unreachable or its shape has changed, the report falls back to
a note flagging the section for MANUAL update from the human speeches page —
never a false "no speeches" report.
"""
import logging
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta
from email.utils import parsedate_to_datetime

import requests

logger = logging.getLogger(__name__)

SPEECHES_RSS_URL = "https://www.federalreserve.gov/feeds/speeches.xml"
SPEECHES_PAGE_URL = "https://www.federalreserve.gov/newsevents/speeches.htm"

# Network timeout (seconds), mirroring the FRED client.
REQUEST_TIMEOUT = 30

DEFAULT_LOOKBACK_DAYS = 14


def _request(url: str) -> str:
    """GET the RSS feed and return the raw response body."""
    response = requests.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.text


class _FeedShapeError(ValueError):
    """The RSS feed returned 200 with an unexpected structure."""


def _parse_items(xml_text: str) -> list[dict]:
    """Parse the verified speeches.xml shape into speech dicts.

    Raises ``_FeedShapeError`` when the feed is not the expected RSS 2.0
    ``channel/item`` structure so the caller falls back loudly.
    """
    root = ET.fromstring(xml_text)
    if root.tag != "rss":
        raise _FeedShapeError(f"expected <rss>, got <{root.tag}>")
    channel = root.find("channel")
    if channel is None:
        raise _FeedShapeError("no <channel> element")
    items = []
    for item in channel.findall("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub = (item.findtext("pubDate") or "").strip()
        if not title or not pub:
            continue
        speaker, _, talk = title.partition(", ")
        # description is the venue line, e.g. "Speech At the Exchequer Club".
        summary = (item.findtext("description") or "").strip()
        items.append(
            {
                "speaker": speaker if talk else "",
                "title": talk or title,
                "link": link,
                "summary": summary,
                "date": parsedate_to_datetime(pub).date(),
            }
        )
    return items


def _fallback(curr_date: str, start: date, reason: str) -> str:
    return (
        "## Recent Fed Speeches\n"
        f"- Source: Federal Reserve RSS feed ({SPEECHES_RSS_URL})\n"
        f"- Window: {start} to {curr_date}\n"
        f"\n**RSS feed unavailable** ({reason}). This section needs a MANUAL "
        f"update: review recent Fed speeches at {SPEECHES_PAGE_URL} for the "
        "window above.\n"
    )


def get_fed_speeches(curr_date: str, look_back_days: int = DEFAULT_LOOKBACK_DAYS) -> str:
    """Fetch recent Fed official speeches as a markdown report.

    Args:
        curr_date: The as-of date (yyyy-mm-dd). Speeches published after it
            are excluded, so a historical run never sees future speeches.
        look_back_days: Trailing window length (default 14).

    Returns:
        A markdown table of in-window speeches (most recent first), an
        explicit no-speeches note, or a manual-update fallback when the feed
        is unreachable or its shape changed.
    """
    end_dt = datetime.strptime(curr_date, "%Y-%m-%d").date()
    start_dt = end_dt - timedelta(days=look_back_days)

    try:
        items = _parse_items(_request(SPEECHES_RSS_URL))
    except (requests.RequestException, ET.ParseError, _FeedShapeError) as e:
        logger.warning("Fed speeches feed unavailable: %s", e)
        return _fallback(curr_date, start_dt, e)

    window = [s for s in items if start_dt <= s["date"] <= end_dt]
    window.sort(key=lambda s: s["date"], reverse=True)

    header = (
        "## Recent Fed Speeches\n"
        f"- Source: Federal Reserve RSS feed ({SPEECHES_RSS_URL})\n"
        f"- Window: {start_dt} to {end_dt}\n"
    )
    if not window:
        return header + (
            "\nNo Fed speeches in this window. The RSS feed only carries the "
            "most recent speeches, so windows far in the past are normally "
            "empty.\n"
        )

    table = (
        "\n| Date | Speaker | Title | Venue | Link |\n"
        "| --- | --- | --- | --- | --- |\n"
        + "\n".join(
            f"| {s['date']} | {s['speaker']} | {s['title']} | {s['summary']} "
            f"| {s['link']} |"
            for s in window
        )
        + "\n"
    )
    return header + table
