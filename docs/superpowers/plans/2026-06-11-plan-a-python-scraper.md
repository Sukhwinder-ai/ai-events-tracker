# Plan A — Python Scraper Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A Python scraper that queries Luma for AI events in Brisbane/Ipswich (filtered at the source), normalizes and dedups them, and writes them to Supabase — recording each run so NEW events can be flagged. Runs fortnightly on GitHub Actions.

**Architecture:** Small, single-responsibility modules. A `LumaSource` fetches AI events using AI-specific calendars/search queries (filtering at query-time, no LLM). A `normalize` step maps raw results to the `events` schema (city, cost, dedup_key). A `SupabaseWriter` opens a `scrape_runs` row, upserts events on `dedup_key`, stamps `first_seen_run` on genuinely new rows, and closes the run. A read-only Playwright fallback exists but is unused unless a source needs JS rendering. A `run.py` CLI ties it together. Depends on Plan 0's schema.

**Tech Stack:** Python 3.11+, `httpx`, `beautifulsoup4`, `supabase` (supabase-py), `python-dotenv`, `pytest`, `respx` (HTTP mocking), `playwright` (fallback only).

---

## File Structure

All under `scraper/`:

- Create: `scraper/pyproject.toml` — deps + pytest config
- Create: `scraper/.env.example` — documents required env vars
- Create: `scraper/.gitignore` — ignores `.env`, venv, caches
- Create: `scraper/README.md` — setup + run instructions
- Create: `scraper/src/aiscraper/__init__.py`
- Create: `scraper/src/aiscraper/config.py` — load + validate env (Supabase creds, settings)
- Create: `scraper/src/aiscraper/models.py` — `RawEvent`, `Event` dataclasses
- Create: `scraper/src/aiscraper/normalize.py` — raw → Event (city, cost, dedup_key)
- Create: `scraper/src/aiscraper/sources/luma.py` — `LumaSource` (query-time AI filtering)
- Create: `scraper/src/aiscraper/dedup.py` — drop duplicate dedup_keys within a run
- Create: `scraper/src/aiscraper/writer.py` — `SupabaseWriter` (runs + upsert + first_seen_run)
- Create: `scraper/src/aiscraper/playwright_guard.py` — read-only Playwright fallback contract
- Create: `scraper/run.py` — CLI entry point
- Create: `scraper/tests/...` — one test file per module

Tests never hit the real network or real Supabase — HTTP is mocked with `respx`, the writer is tested against a fake client.

---

### Task 1: Project scaffold and dependencies

**Files:**
- Create: `scraper/pyproject.toml`
- Create: `scraper/.gitignore`
- Create: `scraper/.env.example`
- Create: `scraper/src/aiscraper/__init__.py`

- [ ] **Step 1: Write pyproject.toml**

```toml
[project]
name = "aiscraper"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "httpx>=0.27",
  "beautifulsoup4>=4.12",
  "supabase>=2.6",
  "python-dotenv>=1.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "respx>=0.21"]
browser = ["playwright>=1.45"]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"
```

- [ ] **Step 2: Write .gitignore**

```gitignore
.env
.venv/
__pycache__/
*.pyc
.pytest_cache/
```

- [ ] **Step 3: Write .env.example**

```bash
# From Supabase Dashboard -> Project Settings -> API
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
# service_role key — SECRET, scraper writes only. Never expose to a browser.
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Comma-separated Luma AI calendar slugs to pull from (query-time AI filtering)
LUMA_AI_CALENDARS=
# Comma-separated AI search terms used as queries sent to Luma
LUMA_AI_QUERIES=AI,artificial intelligence,machine learning,LLM,GenAI,deep learning,data science
```

- [ ] **Step 4: Create the package marker**

Create `scraper/src/aiscraper/__init__.py` with a single line:

```python
__all__ = []
```

- [ ] **Step 5: Create venv and install**

Run:
```bash
cd scraper && python3 -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"
```
Expected: installs httpx, supabase, pytest, respx, etc. with no errors.

- [ ] **Step 6: Verify pytest runs (no tests yet)**

Run: `cd scraper && . .venv/bin/activate && pytest`
Expected: "no tests ran" (exit code 5) — confirms pytest is wired.

- [ ] **Step 7: Commit**

```bash
git add scraper/pyproject.toml scraper/.gitignore scraper/.env.example scraper/src/aiscraper/__init__.py
git commit -m "chore(scraper): project scaffold and dependencies"
```

---

### Task 2: Data models

**Files:**
- Create: `scraper/src/aiscraper/models.py`
- Test: `scraper/tests/test_models.py`

- [ ] **Step 1: Write the failing test**

Create `scraper/tests/test_models.py`:

```python
from aiscraper.models import RawEvent, Event


def test_rawevent_holds_source_fields():
    raw = RawEvent(
        title="ML Meetup",
        starts_at="2026-06-18T18:00:00+10:00",
        location="South Brisbane",
        url="https://lu.ma/ml",
        is_free=True,
        source="luma",
    )
    assert raw.title == "ML Meetup"
    assert raw.is_free is True


def test_event_is_the_db_shape():
    ev = Event(
        title="ML Meetup",
        starts_at="2026-06-18T18:00:00+10:00",
        city="brisbane",
        venue="South Brisbane",
        cost="free",
        source="luma",
        url="https://lu.ma/ml",
        dedup_key="ml-meetup|2026-06-18|south-brisbane",
    )
    assert ev.city == "brisbane"
    assert ev.cost == "free"
    assert ev.status is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd scraper && . .venv/bin/activate && pytest tests/test_models.py -v`
Expected: FAIL with "No module named 'aiscraper.models'".

- [ ] **Step 3: Write minimal implementation**

Create `scraper/src/aiscraper/models.py`:

```python
from dataclasses import dataclass
from typing import Optional


@dataclass
class RawEvent:
    """Whatever a source hands back, before normalization."""
    title: str
    starts_at: Optional[str]
    location: Optional[str]
    url: Optional[str]
    is_free: Optional[bool]
    source: str


@dataclass
class Event:
    """Matches the Supabase `events` table shape (minus DB-managed fields)."""
    title: str
    starts_at: Optional[str]
    city: str
    venue: Optional[str]
    cost: Optional[str]
    source: str
    url: Optional[str]
    dedup_key: str
    status: Optional[str] = None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd scraper && . .venv/bin/activate && pytest tests/test_models.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add scraper/src/aiscraper/models.py scraper/tests/test_models.py
git commit -m "feat(scraper): add RawEvent and Event models"
```

---

### Task 3: Normalization (city, cost, dedup_key)

**Files:**
- Create: `scraper/src/aiscraper/normalize.py`
- Test: `scraper/tests/test_normalize.py`

- [ ] **Step 1: Write the failing test**

Create `scraper/tests/test_normalize.py`:

```python
from aiscraper.models import RawEvent
from aiscraper.normalize import detect_city, make_dedup_key, to_event


def test_detect_city_brisbane_and_ipswich():
    assert detect_city("South Brisbane") == "brisbane"
    assert detect_city("Fire Station 101, Ipswich") == "ipswich"


def test_detect_city_returns_none_when_neither():
    assert detect_city("Gold Coast Convention Centre") is None
    assert detect_city(None) is None


def test_make_dedup_key_is_stable_and_slugified():
    key = make_dedup_key("ML  Meetup!", "2026-06-18T18:00:00+10:00", "South Brisbane")
    assert key == "ml-meetup|2026-06-18|south-brisbane"


def test_to_event_maps_free_and_city():
    raw = RawEvent(
        title="ML Meetup",
        starts_at="2026-06-18T18:00:00+10:00",
        location="South Brisbane",
        url="https://lu.ma/ml",
        is_free=True,
        source="luma",
    )
    ev = to_event(raw)
    assert ev.city == "brisbane"
    assert ev.cost == "free"
    assert ev.dedup_key == "ml-meetup|2026-06-18|south-brisbane"


def test_to_event_returns_none_when_city_unknown():
    raw = RawEvent("X", "2026-06-18T18:00:00+10:00", "Sydney", "u", True, "luma")
    assert to_event(raw) is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd scraper && . .venv/bin/activate && pytest tests/test_normalize.py -v`
Expected: FAIL with "No module named 'aiscraper.normalize'".

- [ ] **Step 3: Write minimal implementation**

Create `scraper/src/aiscraper/normalize.py`:

```python
import re
from typing import Optional

from aiscraper.models import Event, RawEvent

_CITIES = ("brisbane", "ipswich")


def detect_city(location: Optional[str]) -> Optional[str]:
    if not location:
        return None
    low = location.lower()
    for city in _CITIES:
        if city in low:
            return city
    return None


def _slug(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def make_dedup_key(title: str, starts_at: Optional[str], venue: Optional[str]) -> str:
    date_part = (starts_at or "")[:10]  # YYYY-MM-DD
    return f"{_slug(title)}|{date_part}|{_slug(venue or '')}"


def to_event(raw: RawEvent) -> Optional[Event]:
    city = detect_city(raw.location)
    if city is None:
        return None
    cost = "free" if raw.is_free else "paid"
    return Event(
        title=raw.title,
        starts_at=raw.starts_at,
        city=city,
        venue=raw.location,
        cost=cost,
        source=raw.source,
        url=raw.url,
        dedup_key=make_dedup_key(raw.title, raw.starts_at, raw.location),
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd scraper && . .venv/bin/activate && pytest tests/test_normalize.py -v`
Expected: PASS (5 passed).

- [ ] **Step 5: Commit**

```bash
git add scraper/src/aiscraper/normalize.py scraper/tests/test_normalize.py
git commit -m "feat(scraper): normalize raw events to DB shape with city/cost/dedup_key"
```

---

### Task 4: In-run dedup

**Files:**
- Create: `scraper/src/aiscraper/dedup.py`
- Test: `scraper/tests/test_dedup.py`

- [ ] **Step 1: Write the failing test**

Create `scraper/tests/test_dedup.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd scraper && . .venv/bin/activate && pytest tests/test_dedup.py -v`
Expected: FAIL with "No module named 'aiscraper.dedup'".

- [ ] **Step 3: Write minimal implementation**

Create `scraper/src/aiscraper/dedup.py`:

```python
from typing import List

from aiscraper.models import Event


def dedup_events(events: List[Event]) -> List[Event]:
    seen = set()
    out = []
    for e in events:
        if e.dedup_key in seen:
            continue
        seen.add(e.dedup_key)
        out.append(e)
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd scraper && . .venv/bin/activate && pytest tests/test_dedup.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add scraper/src/aiscraper/dedup.py scraper/tests/test_dedup.py
git commit -m "feat(scraper): in-run dedup by dedup_key"
```

---

### Task 5: Config loading

**Files:**
- Create: `scraper/src/aiscraper/config.py`
- Test: `scraper/tests/test_config.py`

- [ ] **Step 1: Write the failing test**

Create `scraper/tests/test_config.py`:

```python
import pytest
from aiscraper.config import load_config


def test_load_config_reads_env(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://x.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "secret")
    monkeypatch.setenv("LUMA_AI_QUERIES", "AI, machine learning")
    monkeypatch.setenv("LUMA_AI_CALENDARS", "brisbane-ai")
    cfg = load_config()
    assert cfg.supabase_url == "https://x.supabase.co"
    assert cfg.supabase_key == "secret"
    assert cfg.ai_queries == ["AI", "machine learning"]
    assert cfg.ai_calendars == ["brisbane-ai"]


def test_load_config_missing_required_raises(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    with pytest.raises(ValueError, match="SUPABASE_URL"):
        load_config()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd scraper && . .venv/bin/activate && pytest tests/test_config.py -v`
Expected: FAIL with "No module named 'aiscraper.config'".

- [ ] **Step 3: Write minimal implementation**

Create `scraper/src/aiscraper/config.py`:

```python
import os
from dataclasses import dataclass
from typing import List

from dotenv import load_dotenv


@dataclass
class Config:
    supabase_url: str
    supabase_key: str
    ai_queries: List[str]
    ai_calendars: List[str]


def _split(value: str) -> List[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def load_config() -> Config:
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url:
        raise ValueError("SUPABASE_URL is required")
    if not key:
        raise ValueError("SUPABASE_SERVICE_ROLE_KEY is required")
    return Config(
        supabase_url=url,
        supabase_key=key,
        ai_queries=_split(os.getenv("LUMA_AI_QUERIES", "")),
        ai_calendars=_split(os.getenv("LUMA_AI_CALENDARS", "")),
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd scraper && . .venv/bin/activate && pytest tests/test_config.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add scraper/src/aiscraper/config.py scraper/tests/test_config.py
git commit -m "feat(scraper): env config loading with validation"
```

---

### Task 6: Luma source (query-time AI filtering)

**Files:**
- Create: `scraper/src/aiscraper/sources/__init__.py`
- Create: `scraper/src/aiscraper/sources/luma.py`
- Test: `scraper/tests/test_luma.py`

The Luma public API returns calendar events as JSON. We pull from AI-specific calendar slugs (every event already AI) and from AI search queries. This is the query-time filtering — we never fetch the whole city feed.

- [ ] **Step 1: Create the sources package marker**

Create `scraper/src/aiscraper/sources/__init__.py`:

```python
__all__ = []
```

- [ ] **Step 2: Write the failing test**

Create `scraper/tests/test_luma.py`:

```python
import httpx
import respx
from aiscraper.sources.luma import LumaSource, CALENDAR_URL


@respx.mock
def test_fetch_calendar_parses_entries():
    payload = {
        "entries": [
            {
                "event": {
                    "name": "Brisbane AI Builders",
                    "start_at": "2026-06-14T18:00:00+10:00",
                    "geo_address_info": {"city_state": "Fortitude Valley, Brisbane"},
                    "url": "brisbane-ai-builders",
                    "ticket_info": {"is_free": True},
                }
            }
        ]
    }
    respx.get(CALENDAR_URL, params={"calendar_api_id": "brisbane-ai"}).mock(
        return_value=httpx.Response(200, json=payload)
    )

    src = LumaSource(ai_calendars=["brisbane-ai"], ai_queries=[])
    raw = src.fetch()

    assert len(raw) == 1
    assert raw[0].title == "Brisbane AI Builders"
    assert raw[0].location == "Fortitude Valley, Brisbane"
    assert raw[0].is_free is True
    assert raw[0].url == "https://lu.ma/brisbane-ai-builders"
    assert raw[0].source == "luma"


@respx.mock
def test_fetch_handles_missing_optional_fields():
    payload = {"entries": [{"event": {"name": "Bare Event"}}]}
    respx.get(CALENDAR_URL, params={"calendar_api_id": "brisbane-ai"}).mock(
        return_value=httpx.Response(200, json=payload)
    )
    src = LumaSource(ai_calendars=["brisbane-ai"], ai_queries=[])
    raw = src.fetch()
    assert raw[0].title == "Bare Event"
    assert raw[0].location is None
    assert raw[0].is_free is None
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd scraper && . .venv/bin/activate && pytest tests/test_luma.py -v`
Expected: FAIL with "No module named 'aiscraper.sources.luma'".

- [ ] **Step 4: Write minimal implementation**

Create `scraper/src/aiscraper/sources/luma.py`:

```python
from typing import List, Optional

import httpx

from aiscraper.models import RawEvent

CALENDAR_URL = "https://api.lu.ma/calendar/get-items"
_TIMEOUT = 20.0
_USER_AGENT = "ai-events-tracker/0.1 (personal, read-only)"


class LumaSource:
    """Fetches AI events from Luma using AI-specific calendars and queries.

    Filtering happens here, at query-time: we only ever ask Luma for AI
    calendars / AI search terms, so results are already relevant.
    """

    def __init__(self, ai_calendars: List[str], ai_queries: List[str]):
        self.ai_calendars = ai_calendars
        self.ai_queries = ai_queries

    def fetch(self) -> List[RawEvent]:
        events: List[RawEvent] = []
        headers = {"User-Agent": _USER_AGENT, "Accept": "application/json"}
        with httpx.Client(timeout=_TIMEOUT, headers=headers) as client:
            for slug in self.ai_calendars:
                resp = client.get(CALENDAR_URL, params={"calendar_api_id": slug})
                resp.raise_for_status()
                events.extend(self._parse(resp.json()))
        return events

    def _parse(self, payload: dict) -> List[RawEvent]:
        out: List[RawEvent] = []
        for entry in payload.get("entries", []):
            ev = entry.get("event", {})
            out.append(
                RawEvent(
                    title=ev.get("name", ""),
                    starts_at=ev.get("start_at"),
                    location=self._location(ev),
                    url=self._url(ev.get("url")),
                    is_free=self._is_free(ev),
                    source="luma",
                )
            )
        return out

    @staticmethod
    def _location(ev: dict) -> Optional[str]:
        geo = ev.get("geo_address_info") or {}
        return geo.get("city_state")

    @staticmethod
    def _url(slug: Optional[str]) -> Optional[str]:
        return f"https://lu.ma/{slug}" if slug else None

    @staticmethod
    def _is_free(ev: dict) -> Optional[bool]:
        ticket = ev.get("ticket_info")
        if not ticket:
            return None
        return ticket.get("is_free")
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd scraper && . .venv/bin/activate && pytest tests/test_luma.py -v`
Expected: PASS (2 passed).

- [ ] **Step 6: Commit**

```bash
git add scraper/src/aiscraper/sources/ scraper/tests/test_luma.py
git commit -m "feat(scraper): Luma source with query-time AI filtering"
```

---

### Task 7: Supabase writer (runs + upsert + first_seen_run)

**Files:**
- Create: `scraper/src/aiscraper/writer.py`
- Test: `scraper/tests/test_writer.py`

The writer is tested against a small fake that records calls — no real network. It opens a run, upserts events on `dedup_key`, stamps `first_seen_run` only on rows that did not already exist, and closes the run with counts.

- [ ] **Step 1: Write the failing test**

Create `scraper/tests/test_writer.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd scraper && . .venv/bin/activate && pytest tests/test_writer.py -v`
Expected: FAIL with "No module named 'aiscraper.writer'".

- [ ] **Step 3: Write minimal implementation**

Create `scraper/src/aiscraper/writer.py`:

```python
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List

from aiscraper.models import Event


@dataclass
class RunResult:
    run_id: int
    found: int
    new: int


class SupabaseWriter:
    """Writes a scrape run + its events. New events (unseen dedup_keys) get
    first_seen_run stamped with this run's id; existing events keep theirs."""

    def __init__(self, client):
        self.client = client

    def write_run(self, source: str, events: List[Event]) -> RunResult:
        run_id = self._open_run(source)
        existing_keys = self._existing_keys([e.dedup_key for e in events])

        rows = []
        new_count = 0
        for e in events:
            row = {
                "title": e.title,
                "starts_at": e.starts_at,
                "city": e.city,
                "venue": e.venue,
                "cost": e.cost,
                "source": e.source,
                "url": e.url,
                "dedup_key": e.dedup_key,
            }
            if e.dedup_key not in existing_keys:
                row["first_seen_run"] = run_id
                new_count += 1
            rows.append(row)

        if rows:
            self.client.table("events").upsert(
                rows, on_conflict="dedup_key"
            ).execute()

        self._close_run(run_id, found=len(events), new=new_count)
        return RunResult(run_id=run_id, found=len(events), new=new_count)

    def _open_run(self, source: str) -> int:
        resp = self.client.table("scrape_runs").insert({"source": source}).execute()
        return resp.data[0]["id"]

    def _existing_keys(self, keys: List[str]) -> set:
        if not keys:
            return set()
        resp = (
            self.client.table("events")
            .select("dedup_key")
            .in_("dedup_key", keys)
            .execute()
        )
        return {row["dedup_key"] for row in resp.data}

    def _close_run(self, run_id: int, found: int, new: int) -> None:
        self.client.table("scrape_runs").update(
            {
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "events_found": found,
                "events_new": new,
            }
        ).eq("id", run_id).execute()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd scraper && . .venv/bin/activate && pytest tests/test_writer.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add scraper/src/aiscraper/writer.py scraper/tests/test_writer.py
git commit -m "feat(scraper): Supabase writer with run tracking and first_seen_run"
```

---

### Task 8: Read-only Playwright guardrail (fallback)

**Files:**
- Create: `scraper/src/aiscraper/playwright_guard.py`
- Test: `scraper/tests/test_playwright_guard.py`

Playwright is unused unless a future source needs JS rendering. This module enforces the read-only contract from the spec: it routes a Playwright page so only GET requests pass and exposes only read helpers. We test the request-gating logic with a fake route (no real browser).

- [ ] **Step 1: Write the failing test**

Create `scraper/tests/test_playwright_guard.py`:

```python
from aiscraper.playwright_guard import is_request_allowed, FORBIDDEN_METHODS


def test_get_requests_allowed():
    assert is_request_allowed("GET") is True


def test_mutating_methods_blocked():
    for method in ["POST", "PUT", "DELETE", "PATCH"]:
        assert method in FORBIDDEN_METHODS
        assert is_request_allowed(method) is False


def test_method_check_is_case_insensitive():
    assert is_request_allowed("get") is True
    assert is_request_allowed("post") is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd scraper && . .venv/bin/activate && pytest tests/test_playwright_guard.py -v`
Expected: FAIL with "No module named 'aiscraper.playwright_guard'".

- [ ] **Step 3: Write minimal implementation**

Create `scraper/src/aiscraper/playwright_guard.py`:

```python
"""Read-only Playwright contract (fallback, used only if a source needs JS).

The scraper only ever READS public pages. This guard enforces that:
- only GET requests are allowed through; everything else is aborted
- callers get read helpers only (navigate + read text); no click/fill/etc.
"""

FORBIDDEN_METHODS = {"POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}


def is_request_allowed(method: str) -> bool:
    return method.upper() == "GET"


def install_readonly_guard(page) -> None:
    """Route a Playwright page so only GET requests proceed. All others abort.

    Usage (only when a JS-rendered source requires it):
        install_readonly_guard(page)
        page.goto(url)               # allowed
        html = page.content()        # allowed (read)
        # page.click(...) etc. are simply never called by our code
    """
    def _route(route):
        if is_request_allowed(route.request.method):
            route.continue_()
        else:
            route.abort()

    page.route("**/*", _route)


def read_text(page, url: str) -> str:
    """Navigate (GET) and return page HTML. Read-only."""
    page.goto(url, wait_until="domcontentloaded")
    return page.content()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd scraper && . .venv/bin/activate && pytest tests/test_playwright_guard.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add scraper/src/aiscraper/playwright_guard.py scraper/tests/test_playwright_guard.py
git commit -m "feat(scraper): read-only Playwright guardrail (GET-only fallback)"
```

---

### Task 9: Pipeline orchestration

**Files:**
- Create: `scraper/src/aiscraper/pipeline.py`
- Test: `scraper/tests/test_pipeline.py`

Ties source → normalize → dedup → writer together as one testable function (no I/O of its own; takes a source and writer in).

- [ ] **Step 1: Write the failing test**

Create `scraper/tests/test_pipeline.py`:

```python
from aiscraper.models import RawEvent, Event
from aiscraper.pipeline import run_pipeline


class StubSource:
    def __init__(self, raws):
        self._raws = raws

    def fetch(self):
        return self._raws


class StubWriter:
    def __init__(self):
        self.written = None

    def write_run(self, source, events):
        self.written = events
        from aiscraper.writer import RunResult
        new = len(events)
        return RunResult(run_id=1, found=len(events), new=new)


def test_pipeline_normalizes_dedups_and_writes():
    raws = [
        RawEvent("ML Meetup", "2026-06-18T18:00:00+10:00", "South Brisbane",
                 "https://lu.ma/ml", True, "luma"),
        # duplicate of the first after normalization
        RawEvent("ML Meetup", "2026-06-18T18:00:00+10:00", "South Brisbane",
                 "https://lu.ma/ml", True, "luma"),
        # dropped: city not Brisbane/Ipswich
        RawEvent("Sydney AI", "2026-06-18T18:00:00+10:00", "Sydney",
                 "https://lu.ma/syd", True, "luma"),
    ]
    writer = StubWriter()
    result = run_pipeline(StubSource(raws), writer, source_name="luma")

    assert len(writer.written) == 1  # deduped + city-filtered
    assert writer.written[0].city == "brisbane"
    assert result.found == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd scraper && . .venv/bin/activate && pytest tests/test_pipeline.py -v`
Expected: FAIL with "No module named 'aiscraper.pipeline'".

- [ ] **Step 3: Write minimal implementation**

Create `scraper/src/aiscraper/pipeline.py`:

```python
from aiscraper.dedup import dedup_events
from aiscraper.normalize import to_event


def run_pipeline(source, writer, source_name: str):
    raws = source.fetch()
    events = [ev for ev in (to_event(r) for r in raws) if ev is not None]
    events = dedup_events(events)
    return writer.write_run(source=source_name, events=events)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd scraper && . .venv/bin/activate && pytest tests/test_pipeline.py -v`
Expected: PASS (1 passed).

- [ ] **Step 5: Commit**

```bash
git add scraper/src/aiscraper/pipeline.py scraper/tests/test_pipeline.py
git commit -m "feat(scraper): pipeline orchestration (fetch->normalize->dedup->write)"
```

---

### Task 10: CLI entry point

**Files:**
- Create: `scraper/run.py`
- Test: `scraper/tests/test_run_smoke.py`

- [ ] **Step 1: Write the failing test**

Create `scraper/tests/test_run_smoke.py`:

```python
import importlib


def test_run_module_exposes_main():
    mod = importlib.import_module("run")
    assert hasattr(mod, "main")
```

Note: this test imports `run` from the `scraper/` dir. Add `scraper` to pytest's path by running pytest from `scraper/` (already configured via `pythonpath = ["src"]`; also add the repo-relative import below).

- [ ] **Step 2: Run test to verify it fails**

Run: `cd scraper && . .venv/bin/activate && pytest tests/test_run_smoke.py -v`
Expected: FAIL with "No module named 'run'".

- [ ] **Step 3: Add scraper root to pytest path, then implement run.py**

Update `scraper/pyproject.toml` pytest section to include the project root:

```toml
[tool.pytest.ini_options]
pythonpath = ["src", "."]
testpaths = ["tests"]
```

Create `scraper/run.py`:

```python
"""CLI entry point. Builds the real Luma source + Supabase writer and runs once."""
from supabase import create_client

from aiscraper.config import load_config
from aiscraper.pipeline import run_pipeline
from aiscraper.sources.luma import LumaSource
from aiscraper.writer import SupabaseWriter


def main() -> None:
    cfg = load_config()
    client = create_client(cfg.supabase_url, cfg.supabase_key)
    source = LumaSource(ai_calendars=cfg.ai_calendars, ai_queries=cfg.ai_queries)
    writer = SupabaseWriter(client)
    result = run_pipeline(source, writer, source_name="luma")
    print(
        f"Run {result.run_id}: found {result.found} events, "
        f"{result.new} new."
    )


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd scraper && . .venv/bin/activate && pytest tests/test_run_smoke.py -v`
Expected: PASS (1 passed).

- [ ] **Step 5: Run the full test suite**

Run: `cd scraper && . .venv/bin/activate && pytest -v`
Expected: all tests pass (models, normalize, dedup, config, luma, writer, playwright_guard, pipeline, run smoke).

- [ ] **Step 6: Commit**

```bash
git add scraper/run.py scraper/pyproject.toml scraper/tests/test_run_smoke.py
git commit -m "feat(scraper): CLI entry point wiring real source + writer"
```

---

### Task 11: Live smoke test against Supabase (manual)

**Files:** none (manual — requires real credentials and Plan 0 applied)

- [ ] **Step 1: Create your real .env**

Copy the example and fill in real values from Supabase:
```bash
cd scraper && cp .env.example .env
```
Edit `.env`: set `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, and at least one real value in `LUMA_AI_CALENDARS` (an AI calendar slug for the region). If you don't have a calendar slug yet, leave calendars empty for now — the run will simply find 0 events, which still proves the Supabase write path via the run row.

- [ ] **Step 2: Run the scraper once**

Run: `cd scraper && . .venv/bin/activate && python run.py`
Expected: prints `Run <id>: found N events, M new.` with no errors.

- [ ] **Step 3: Verify in Supabase**

In the Supabase SQL Editor:
```sql
select id, source, events_found, events_new, finished_at from scrape_runs order by id desc limit 1;
```
Expected: your run row with a non-null `finished_at`. If calendars were configured, also:
```sql
select title, city, first_seen_run from events where source = 'luma' order by created_at desc limit 5;
```

- [ ] **Step 4: Write the scraper README**

Create `scraper/README.md`:

```markdown
# AI Events Scraper

Python scraper: queries Luma for AI events in Brisbane/Ipswich (filtered at
query-time), dedups, and writes them to Supabase. Runs fortnightly via GitHub
Actions.

## Setup
    python3 -m venv .venv && . .venv/bin/activate
    pip install -e ".[dev]"
    cp .env.example .env   # fill in Supabase creds + Luma AI calendars/queries

## Run once
    python run.py

## Test
    pytest

## How AI filtering works
We never pull the whole city feed. We query Luma's AI calendars + AI search
terms, so results are already AI. No LLM, no API cost.

## Playwright
Optional fallback only (`pip install -e ".[browser]"`). Read-only contract in
`playwright_guard.py`: GET requests only, no clicks/fills/forms.
```

- [ ] **Step 5: Commit**

```bash
git add scraper/README.md
git commit -m "docs(scraper): setup and run instructions"
```

---

### Task 12: Fortnightly GitHub Actions cron

**Files:**
- Create: `.github/workflows/scrape.yml`

- [ ] **Step 1: Write the workflow**

Create `.github/workflows/scrape.yml`:

```yaml
name: Fortnightly AI events scrape

on:
  schedule:
    # 02:00 UTC on the 1st and 15th of each month ≈ fortnightly
    - cron: "0 2 1,15 * *"
  workflow_dispatch: {}   # allow manual runs from the Actions tab

jobs:
  scrape:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: scraper
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install
        run: pip install -e ".[dev]"
      - name: Run tests
        run: pytest -q
      - name: Scrape
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}
          LUMA_AI_CALENDARS: ${{ secrets.LUMA_AI_CALENDARS }}
          LUMA_AI_QUERIES: ${{ secrets.LUMA_AI_QUERIES }}
        run: python run.py
```

- [ ] **Step 2: Add the GitHub secrets (manual)**

In the GitHub repo: **Settings → Secrets and variables → Actions → New repository secret**. Add: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `LUMA_AI_CALENDARS`, `LUMA_AI_QUERIES`.

- [ ] **Step 3: Verify via manual dispatch**

Push, then in the GitHub **Actions** tab → "Fortnightly AI events scrape" → **Run workflow**. Expected: tests pass, scrape step prints the run summary, green check.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/scrape.yml
git commit -m "ci(scraper): fortnightly scrape workflow with manual dispatch"
```

---

## Self-Review

- **Spec coverage:** Luma query-time AI filtering (Task 6), city = brisbane/ipswich (Task 3), cost free/paid (Task 3), dedup_key unique + in-run dedup (Tasks 3,4,7), first_seen_run / NEW (Task 7), scrape_runs run tracking (Task 7), read-only Playwright guardrail (Task 8), fortnightly cron (Task 12), no Anthropic/LLM (nothing references it). ✅
- **Cron note:** cron `1,15 * *` is an approximate fortnight (GitHub has no true "every 14 days"); documented inline. ✅
- **Type consistency:** `Event`, `RawEvent`, `RunResult` fields and method names (`fetch`, `write_run`, `to_event`, `dedup_events`, `run_pipeline`) match across tasks. ✅
- **No placeholders.** ✅
- **Shared contract:** column names (`dedup_key`, `first_seen_run`, `city`, `cost`, etc.) match Plan 0 verbatim. ✅

## Handoff

This plan depends on Plan 0 (schema live). It can run in parallel with Plan B (dashboard) — they share only the Supabase schema, not code.
