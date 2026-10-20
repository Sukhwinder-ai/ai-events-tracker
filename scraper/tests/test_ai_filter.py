from types import SimpleNamespace

import pytest

from aiscraper.ai_filter import Verdicts, ai_filter, classify_titles
from aiscraper.models import Event


def _ev(title):
    return Event(title=title, starts_at=None, city="brisbane", venue=None,
                 cost=None, source="luma", url=None, dedup_key=title)


class FakeMessages:
    def __init__(self, keep=None, stop_reason="end_turn", raise_exc=None):
        self._keep = keep
        self._stop = stop_reason
        self._raise = raise_exc
        self.calls = []

    def parse(self, **kwargs):
        self.calls.append(kwargs)
        if self._raise:
            raise self._raise
        parsed = None if self._keep is None else Verdicts(keep=self._keep)
        return SimpleNamespace(stop_reason=self._stop, parsed_output=parsed)


def fake_client(**kw):
    return SimpleNamespace(messages=FakeMessages(**kw))


def test_drops_only_events_marked_false():
    events = [_ev("Claude Code Workshop"), _ev("Pencil Figure Sketching"),
              _ev("AWS User Group")]
    client = fake_client(keep=[True, False, True])
    kept, rejected = ai_filter(events, client=client)
    assert [e.title for e in kept] == ["Claude Code Workshop", "AWS User Group"]
    assert [e.title for e in rejected] == ["Pencil Figure Sketching"]


def test_one_api_call_per_run_with_all_titles_numbered():
    events = [_ev("A"), _ev("B"), _ev("C")]
    client = fake_client(keep=[True, True, True])
    ai_filter(events, client=client)
    assert len(client.messages.calls) == 1
    content = client.messages.calls[0]["messages"][0]["content"]
    assert "1. A" in content and "3. C" in content
    assert client.messages.calls[0]["output_format"] is Verdicts


def test_fails_open_on_api_error():
    events = [_ev("A"), _ev("B")]
    client = fake_client(raise_exc=RuntimeError("boom"))
    assert ai_filter(events, client=client) == (events, [])


def test_fails_open_on_refusal():
    events = [_ev("A")]
    client = fake_client(keep=[False], stop_reason="refusal")
    assert ai_filter(events, client=client) == (events, [])


def test_fails_open_on_wrong_verdict_count():
    events = [_ev("A"), _ev("B")]
    client = fake_client(keep=[True])
    assert ai_filter(events, client=client) == (events, [])


def test_skips_without_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert classify_titles(["A"]) is None


def test_empty_input_makes_no_call():
    client = fake_client(keep=[])
    assert ai_filter([], client=client) == ([], [])
    assert client.messages.calls == []


def test_all_false_answer_is_treated_as_bad_and_rejects_nothing():
    events = [_ev("A"), _ev("B")]
    client = fake_client(keep=[False, False])
    assert ai_filter(events, client=client) == (events, [])


def test_rejecting_too_large_a_share_is_treated_as_a_bad_answer():
    events = [_ev(f"E{i}") for i in range(10)]
    client = fake_client(keep=[True] * 6 + [False] * 4)  # 40% > 30%
    assert ai_filter(events, client=client) == (events, [])


def test_rejecting_a_small_share_is_applied():
    events = [_ev(f"E{i}") for i in range(10)]
    client = fake_client(keep=[True] * 8 + [False] * 2)  # 20%
    kept, rejected = ai_filter(events, client=client)
    assert len(kept) == 8 and len(rejected) == 2
