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
import json
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
    """GET the RSS feed and return the decoded response body (stripping any UTF-8 BOM)."""
    response = requests.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    # The Fed RSS feed serves a UTF-8 BOM (\xef\xbb\xbf) which breaks xml.etree.ElementTree.fromstring
    # when decoded as plain text with standard utf-8. utf-8-sig strips the BOM cleanly.
    return response.content.decode("utf-8-sig")


SPEECHES_JSON_URL = "https://www.federalreserve.gov/json/ne-speeches.json"


def _request_json(url: str) -> list[dict]:
    """GET the JSON speeches endpoint and return the parsed list (handling UTF-8 BOM)."""
    response = requests.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    # The Fed's ne-speeches.json serves a UTF-8 BOM (\xef\xbb\xbf). Standard response.json()
    # crashes with "Unexpected UTF-8 BOM (decode using utf-8-sig)".
    return json.loads(response.content.decode("utf-8-sig"))


def _parse_json_items(data: list[dict]) -> list[dict]:
    """Parse the Fed's JSON speeches array into the same dict format as RSS.

    Each JSON object has keys: d (date str), t (title), s (speaker),
    lo (location), l (relative link path).
    """
    items = []
    for entry in data:
        raw_date = entry.get("d", "")
        title = entry.get("t", "").strip()
        speaker = entry.get("s", "").strip()
        location = entry.get("lo", "").strip()
        rel_link = entry.get("l", "").strip()
        if not raw_date or not title:
            continue
        try:
            day = datetime.strptime(raw_date.split(" ")[0], "%m/%d/%Y").date()
        except ValueError:
            continue
        link = f"https://www.federalreserve.gov{rel_link}" if rel_link else ""
        items.append(
            {
                "speaker": speaker,
                "title": title,
                "link": link,
                "summary": location,
                "date": day,
            }
        )
    return items


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
        try:
            day = parsedate_to_datetime(pub).date()
        except ValueError as e:
            raise _FeedShapeError(f"unparseable pubDate {pub!r}: {e}") from e
        items.append(
            {
                "speaker": speaker if talk else "",
                "title": talk or title,
                "link": link,
                "summary": summary,
                "date": day,
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

    Tries the RSS feed first, then falls back to the JSON endpoint at
    /json/ne-speeches.json if the RSS feed is unavailable.

    Args:
        curr_date: The as-of date (yyyy-mm-dd). Speeches published after it
            are excluded, so a historical run never sees future speeches.
        look_back_days: Trailing window length (default 14).

    Returns:
        A markdown table of in-window speeches (most recent first), an
        explicit no-speeches note, or a manual-update fallback when both
        sources are unreachable.
    """
    end_dt = datetime.strptime(curr_date, "%Y-%m-%d").date()
    start_dt = end_dt - timedelta(days=look_back_days)

    items = None
    source_label = "RSS feed"

    # Stage 1: try RSS
    try:
        items = _parse_items(_request(SPEECHES_RSS_URL))
        source_label = f"RSS feed ({SPEECHES_RSS_URL})"
    except (requests.RequestException, ET.ParseError, _FeedShapeError) as rss_err:
        logger.warning("Fed speeches RSS unavailable: %s; trying JSON fallback", rss_err)

        # Stage 2: try JSON
        try:
            raw = _request_json(SPEECHES_JSON_URL)
            items = _parse_json_items(raw)
            source_label = f"JSON endpoint ({SPEECHES_JSON_URL})"
        except (requests.RequestException, ValueError, TypeError) as json_err:
            logger.warning("Fed speeches JSON also unavailable: %s", json_err)
            return _fallback(curr_date, start_dt, f"RSS: {rss_err}; JSON: {json_err}")

    window = [s for s in items if start_dt <= s["date"] <= end_dt]
    window.sort(key=lambda s: s["date"], reverse=True)

    header = (
        "## Recent Fed Speeches\n"
        f"- Source: {source_label}\n"
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
