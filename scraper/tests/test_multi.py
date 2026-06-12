from aiscraper.models import RawEvent
from aiscraper.sources.multi import MultiSource


class _Fake:
    def __init__(self, events=None, error=None):
        self._events = events or []
        self._error = error

    def fetch(self):
        if self._error:
            raise self._error
        return self._events


def _ev(title):
    return RawEvent(title, None, None, f"https://x/{title}", None, "fake", "brisbane")


def test_aggregates_events_from_all_sources():
    a = _Fake([_ev("A1"), _ev("A2")])
    b = _Fake([_ev("B1")])
    raw = MultiSource([a, b]).fetch()
    assert [r.title for r in raw] == ["A1", "A2", "B1"]


def test_one_failing_source_does_not_sink_the_others():
    good = _Fake([_ev("Good")])
    bad = _Fake(error=RuntimeError("boom"))
    raw = MultiSource([bad, good]).fetch()
    assert [r.title for r in raw] == ["Good"]


def test_empty_when_no_sources():
    assert MultiSource([]).fetch() == []
