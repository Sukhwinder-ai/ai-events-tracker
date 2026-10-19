from aiscraper.writer import SupabaseWriter


class FakeTable:
    def __init__(self, store):
        self.store = store
        self._in = None

    def delete(self):
        return self

    def in_(self, col, vals):
        self._in = (col, list(vals))
        return self

    def execute(self):
        col, vals = self._in
        gone = [r for r in self.store["rows"] if r[col] in vals]
        self.store["rows"] = [r for r in self.store["rows"] if r not in gone]
        return type("R", (), {"data": gone})


class FakeClient:
    def __init__(self, store):
        self.store = store
        self.calls = 0

    def table(self, name):
        assert name == "events"
        self.calls += 1
        return FakeTable(self.store)


def test_remove_keys_deletes_only_listed_dedup_keys():
    store = {"rows": [{"dedup_key": "a"}, {"dedup_key": "b"}, {"dedup_key": "c"}]}
    writer = SupabaseWriter(FakeClient(store))
    assert writer.remove_keys(["a", "c"]) == 2
    assert store["rows"] == [{"dedup_key": "b"}]


def test_remove_keys_empty_list_never_touches_the_database():
    store = {"rows": [{"dedup_key": "a"}]}
    client = FakeClient(store)
    assert SupabaseWriter(client).remove_keys([]) == 0
    assert client.calls == 0
    assert store["rows"] == [{"dedup_key": "a"}]
