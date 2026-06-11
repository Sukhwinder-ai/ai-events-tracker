from aiscraper.models import Event
from aiscraper.writer import SupabaseWriter


class FakeTable:
    def __init__(self, store, name):
        self.store = store
        self.name = name
        self._op = None
        self._payload = None
        self._select_cols = None

    def insert(self, payload):
        self._op = "insert"
        self._payload = payload
        return self

    def upsert(self, payload, on_conflict=None):
        self._op = "upsert"
        self._payload = payload
        self.on_conflict = on_conflict
        return self

    def update(self, payload):
        self._op = "update"
        self._payload = payload
        return self

    def select(self, cols):
        self._op = "select"
        self._select_cols = cols
        return self

    def in_(self, col, values):
        self._filter = (col, values)
        return self

    def eq(self, col, val):
        self._eq = (col, val)
        return self

    def execute(self):
        if self.name == "scrape_runs" and self._op == "insert":
            run = {"id": 42}
            self.store["runs"].append(run)
            return type("R", (), {"data": [run]})
        if self.name == "events" and self._op == "select":
            existing = [{"dedup_key": e["dedup_key"]} for e in self.store["existing"]]
            return type("R", (), {"data": existing})
        if self.name == "events" and self._op == "upsert":
            self.store["upserts"].append(self._payload)
            return type("R", (), {"data": self._payload})
        if self.name == "scrape_runs" and self._op == "update":
            self.store["run_updates"].append(self._payload)
            return type("R", (), {"data": [self._payload]})
        return type("R", (), {"data": []})


class FakeClient:
    def __init__(self, store):
        self.store = store

    def table(self, name):
        return FakeTable(self.store, name)


def _ev(key):
    return Event("t", None, "brisbane", "v", "free", "luma", "u", key)


def test_write_run_stamps_new_events_with_run_id():
    store = {"runs": [], "upserts": [], "run_updates": [],
             "existing": [{"dedup_key": "old"}]}
    writer = SupabaseWriter(FakeClient(store))

    events = [_ev("old"), _ev("new1"), _ev("new2")]
    result = writer.write_run(source="luma", events=events)

    assert result.run_id == 42
    assert result.found == 3
    assert result.new == 2  # only "new1" and "new2" are new

    upserted = store["upserts"][0]
    by_key = {row["dedup_key"]: row for row in upserted}
    assert by_key["new1"]["first_seen_run"] == 42
    assert by_key["new2"]["first_seen_run"] == 42
    # existing event must NOT get its first_seen_run overwritten
    assert "first_seen_run" not in by_key["old"]


def test_write_run_records_counts_on_close():
    store = {"runs": [], "upserts": [], "run_updates": [], "existing": []}
    writer = SupabaseWriter(FakeClient(store))
    writer.write_run(source="luma", events=[_ev("a")])
    update = store["run_updates"][0]
    assert update["events_found"] == 1
    assert update["events_new"] == 1
    assert "finished_at" in update
