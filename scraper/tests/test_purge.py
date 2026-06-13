from aiscraper.writer import SupabaseWriter

BOUNDARY = "2026-06-13T00:00:00+10:00"

# A small fixed catalog spanning past / today / future / undated.
ROWS = [
    {"id": "past1", "starts_at": "2026-06-11T18:00:00+10:00"},
    {"id": "past2", "starts_at": "2026-06-12T23:59:00+10:00"},
    {"id": "today", "starts_at": "2026-06-13T07:00:00+10:00"},
    {"id": "future", "starts_at": "2026-06-20T18:00:00+10:00"},
    {"id": "undated", "starts_at": None},
]


class FakeTable:
    def __init__(self, store, name):
        self.store = store
        self.name = name
        self._op = None
        self._lt = None

    def delete(self):
        self._op = "delete"
        return self

    def lt(self, col, val):
        self._lt = (col, val)
        return self

    def execute(self):
        if self.name == "events" and self._op == "delete":
            col, val = self._lt
            # Mirror Postgres: `col < val` is false for NULLs, so they survive.
            deleted = [
                r for r in self.store["rows"]
                if r.get(col) is not None and r[col] < val
            ]
            self.store["rows"] = [r for r in self.store["rows"] if r not in deleted]
            self.store["delete_filter"] = self._lt
            return type("R", (), {"data": deleted})
        return type("R", (), {"data": []})


class FakeClient:
    def __init__(self, store):
        self.store = store

    def table(self, name):
        return FakeTable(self.store, name)


def _writer():
    store = {"rows": [dict(r) for r in ROWS], "delete_filter": None}
    return SupabaseWriter(FakeClient(store)), store


def test_purge_past_deletes_only_events_before_boundary():
    writer, store = _writer()
    deleted = writer.purge_past(BOUNDARY)
    assert deleted == 2
    assert {r["id"] for r in store["rows"]} == {"today", "future", "undated"}


def test_purge_past_never_touches_today_future_or_undated():
    writer, store = _writer()
    writer.purge_past(BOUNDARY)
    surviving = {r["id"] for r in store["rows"]}
    assert "today" in surviving
    assert "future" in surviving
    assert "undated" in surviving


def test_purge_past_filters_on_starts_at_with_the_boundary():
    writer, store = _writer()
    writer.purge_past(BOUNDARY)
    # The guardrail: the delete is scoped by starts_at < boundary, nothing else.
    assert store["delete_filter"] == ("starts_at", BOUNDARY)


def test_purge_past_returns_zero_when_nothing_is_old():
    writer, store = _writer()
    store["rows"] = [{"id": "future", "starts_at": "2026-07-01T00:00:00+10:00"}]
    assert writer.purge_past(BOUNDARY) == 0
