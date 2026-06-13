from datetime import datetime, timezone

from zoneinfo import ZoneInfo

from aiscraper.dates import start_of_today

BRISBANE = ZoneInfo("Australia/Brisbane")


def test_returns_midnight_today_in_brisbane():
    now = datetime(2026, 6, 13, 9, 0, tzinfo=BRISBANE)
    assert start_of_today(now=now) == "2026-06-13T00:00:00+10:00"


def test_uses_brisbane_calendar_day_even_when_now_is_utc():
    # GitHub Actions runs in UTC. 2026-06-12T20:00Z is already 2026-06-13 06:00
    # in Brisbane, so "today" must be the 13th, not the 12th.
    now = datetime(2026, 6, 12, 20, 0, tzinfo=timezone.utc)
    assert start_of_today(now=now) == "2026-06-13T00:00:00+10:00"


def test_late_evening_brisbane_still_same_day():
    now = datetime(2026, 6, 13, 23, 59, tzinfo=BRISBANE)
    assert start_of_today(now=now) == "2026-06-13T00:00:00+10:00"
