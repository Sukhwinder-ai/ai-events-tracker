from aiscraper.models import Event
from aiscraper.dedup import dedup_events


def _ev(key):
    return Event("t", None, "brisbane", "v", "free", "luma", "u", key)


def test_dedup_drops_repeated_keys_keeping_first():
    events = [_ev("a"), _ev("b"), _ev("a")]
    result = dedup_events(events)
    assert [e.dedup_key for e in result] == ["a", "b"]


def test_dedup_empty_list():
    assert dedup_events([]) == []
