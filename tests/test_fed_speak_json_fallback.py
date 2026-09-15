"""Tests for the Fed speeches JSON fallback (Issue 3, Fix A).

When the RSS feed fails, get_fed_speeches should fall back to the JSON
endpoint at /json/ne-speeches.json and still return speech data.
"""
from datetime import date
from unittest.mock import patch

import pytest
import requests

from fixedincomeagent.dataflows.fed_speeches import (
    _parse_json_items,
    _request,
    _request_json,
    get_fed_speeches,
)


SAMPLE_JSON = [
    {
        "d": "8/28/2026 10:00:00 AM",
        "t": "In Our Time",
        "s": "Chairman Kevin Warsh",
        "lo": "At Jackson Hole, Wyoming",
        "l": "/newsevents/speech/warsh20260828a.htm",
    },
    {
        "d": "9/3/2026 8:30:00 AM",
        "t": "The Economic Outlook",
        "s": "Governor Christopher J. Waller",
        "lo": "At Reuters, Washington, D.C.",
        "l": "/newsevents/speech/waller20260903a.htm",
    },
]


@pytest.mark.unit
def test_parse_json_items_extracts_speeches():
    items = _parse_json_items(SAMPLE_JSON)
    assert len(items) == 2
    warsh = [i for i in items if "Warsh" in i["speaker"]][0]
    assert warsh["date"] == date(2026, 8, 28)
    assert warsh["title"] == "In Our Time"
    assert "warsh20260828a" in warsh["link"]


@pytest.mark.unit
def test_parse_json_items_filters_by_window():
    items = _parse_json_items(SAMPLE_JSON)
    start = date(2026, 8, 25)
    end = date(2026, 8, 31)
    window = [i for i in items if start <= i["date"] <= end]
    assert len(window) == 1
    assert "Warsh" in window[0]["speaker"]


@pytest.mark.unit
@patch("fixedincomeagent.dataflows.fed_speeches._request")
@patch("fixedincomeagent.dataflows.fed_speeches._request_json")
def test_falls_back_to_json_when_rss_fails(mock_json, mock_rss):
    mock_rss.side_effect = requests.ConnectionError("RSS down")
    mock_json.return_value = SAMPLE_JSON
    result = get_fed_speeches("2026-09-04", look_back_days=14)
    assert "Warsh" in result or "Waller" in result
    mock_json.assert_called_once()


@pytest.mark.unit
@patch("fixedincomeagent.dataflows.fed_speeches._request")
@patch("fixedincomeagent.dataflows.fed_speeches._request_json")
def test_fallback_also_fails_returns_manual_note(mock_json, mock_rss):
    mock_rss.side_effect = requests.ConnectionError("RSS down")
    mock_json.side_effect = requests.ConnectionError("JSON also down")
    result = get_fed_speeches("2026-09-04", look_back_days=14)
    assert "unavailable" in result.lower() or "MANUAL" in result


@pytest.mark.unit
@patch("fixedincomeagent.dataflows.fed_speeches.requests.get")
def test_request_json_handles_utf8_bom(mock_get):
    class FakeResponse:
        content = b'\xef\xbb\xbf[{"d": "9/3/2026", "t": "Test Speech", "s": "Waller", "lo": "D.C.", "l": "/test"}]'
        def raise_for_status(self):
            pass

    mock_get.return_value = FakeResponse()
    items = _request_json("https://fake.url")
    assert len(items) == 1
    assert items[0]["t"] == "Test Speech"


@pytest.mark.unit
@patch("fixedincomeagent.dataflows.fed_speeches.requests.get")
def test_request_handles_utf8_bom(mock_get):
    class FakeResponse:
        content = b'\xef\xbb\xbf<rss><channel></channel></rss>'
        def raise_for_status(self):
            pass

    mock_get.return_value = FakeResponse()
    text = _request("https://fake.url")
    assert text.startswith("<rss>")
    assert not text.startswith("\ufeff")
