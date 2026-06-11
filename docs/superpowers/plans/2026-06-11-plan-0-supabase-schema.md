# Plan 0 — Supabase Schema Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the `events` table in Supabase that both the scraper and the dashboard depend on — the shared data contract.

**Architecture:** A single Postgres table in Supabase holds the events catalog plus per-event status marks. The scraper writes rows; the dashboard reads rows and updates the `status` column. AI filtering happens in the scraper at query-time, so this schema stays simple. A `scrape_runs` table records each fortnightly run so "NEW" events (those whose `first_seen_run` equals the latest run) can be identified.

**Tech Stack:** Supabase (Postgres), SQL run via the Supabase SQL Editor.

---

## File Structure

- Create: `db/schema.sql` — the full schema (events + scrape_runs, indexes, constraints). Source of truth, version-controlled.
- Create: `db/seed.sql` — one sample row for smoke-testing reads before the scraper exists.
- Create: `db/README.md` — how to apply the schema and where keys live.

This plan is run-once foundation work. It is mostly SQL plus a manual apply step in the Supabase dashboard, then a connection verification.

---

### Task 1: Write the schema SQL

**Files:**
- Create: `db/schema.sql`

- [ ] **Step 1: Write the schema file**

Create `db/schema.sql` with this exact content:

```sql
-- AI Events Tracker schema
-- Run this in the Supabase SQL Editor (Dashboard -> SQL Editor -> New query).

-- Records each scrape run so we can flag NEW events (first seen in the latest run).
create table if not exists scrape_runs (
  id          bigint generated always as identity primary key,
  source      text not null,                 -- 'luma', 'meetup', etc.
  started_at  timestamptz not null default now(),
  finished_at timestamptz,
  events_found int default 0,
  events_new  int default 0,
  notes       text
);

-- The events catalog plus the friend's status marks.
create table if not exists events (
  id             uuid primary key default gen_random_uuid(),
  title          text not null,
  starts_at      timestamptz,
  city           text not null check (city in ('brisbane', 'ipswich')),
  venue          text,
  cost           text check (cost in ('free', 'paid')),
  source         text not null,              -- 'luma', etc.
  url            text,
  status         text check (status in ('interested', 'attending', 'skip')),
  dedup_key      text not null unique,       -- title + date + venue, blocks duplicates
  first_seen_run bigint references scrape_runs(id), -- NEW when this = latest run id
  created_at     timestamptz not null default now()
);

-- Indexes for the dashboard's common queries.
create index if not exists events_starts_at_idx on events (starts_at);
create index if not exists events_city_idx on events (city);
create index if not exists events_status_idx on events (status);
create index if not exists events_first_seen_run_idx on events (first_seen_run);
```

- [ ] **Step 2: Commit**

```bash
git add db/schema.sql
git commit -m "feat(db): add events + scrape_runs schema"
```

---

### Task 2: Apply the schema in Supabase (manual)

**Files:** none (manual dashboard step)

- [ ] **Step 1: Open the SQL Editor**

In the Supabase dashboard for your project: left sidebar → **SQL Editor** → **New query**.

- [ ] **Step 2: Paste and run**

Paste the entire contents of `db/schema.sql` into the editor and click **Run**.
Expected: "Success. No rows returned." and both tables appear under **Table Editor**.

- [ ] **Step 3: Verify tables exist**

In the SQL Editor, run:

```sql
select table_name from information_schema.tables
where table_schema = 'public' order by table_name;
```

Expected output includes both `events` and `scrape_runs`.

---

### Task 3: Capture connection credentials

**Files:**
- Create: `db/README.md`

- [ ] **Step 1: Find the keys**

In the Supabase dashboard: **Project Settings → API**. Note three values:
- **Project URL** (e.g. `https://abcdxyz.supabase.co`)
- **anon public** key — for the dashboard's read access
- **service_role** key — for the scraper's writes (SECRET — never commit, never ship to the browser)

- [ ] **Step 2: Write db/README.md**

Create `db/README.md`:

```markdown
# Database

Schema lives in `schema.sql`. Apply it via the Supabase dashboard SQL Editor.

## Tables
- `events` — events catalog + status marks (the dashboard reads/writes `status`)
- `scrape_runs` — one row per scrape; used to flag NEW events

## Credentials (from Supabase Dashboard → Project Settings → API)
- Project URL → `SUPABASE_URL` (scraper) / `NEXT_PUBLIC_SUPABASE_URL` (dashboard)
- anon public key → `NEXT_PUBLIC_SUPABASE_ANON_KEY` (dashboard, browser-safe)
- service_role key → `SUPABASE_SERVICE_ROLE_KEY` (scraper only, SECRET — never in the browser)

Never commit real keys. Each subsystem keeps its own `.env` (see its README).
```

- [ ] **Step 3: Commit**

```bash
git add db/README.md
git commit -m "docs(db): document tables and credential mapping"
```

---

### Task 4: Seed one row and verify a read

**Files:**
- Create: `db/seed.sql`

- [ ] **Step 1: Write the seed file**

Create `db/seed.sql`:

```sql
-- A single sample run + event, so the dashboard has something to read
-- before the scraper is wired up. Safe to delete later.
insert into scrape_runs (source, finished_at, events_found, events_new)
values ('seed', now(), 1, 1);

insert into events (title, starts_at, city, venue, cost, source, url, dedup_key, first_seen_run)
values (
  'Brisbane AI Builders — RAG & Agents Night',
  now() + interval '5 days',
  'brisbane',
  'Fortitude Valley',
  'free',
  'seed',
  'https://lu.ma/example',
  'brisbane-ai-builders|2026-06-16|fortitude-valley',
  (select max(id) from scrape_runs)
);
```

- [ ] **Step 2: Run the seed in the SQL Editor**

Paste `db/seed.sql` into a new SQL Editor query and **Run**.
Expected: "Success. 1 row" for each insert.

- [ ] **Step 3: Verify the read**

Run:

```sql
select title, city, cost, first_seen_run from events;
```

Expected: one row — the Brisbane AI Builders event with `city = brisbane`, `cost = free`.

- [ ] **Step 4: Commit**

```bash
git add db/seed.sql
git commit -m "chore(db): add sample seed row for smoke-testing reads"
```

---

## Self-Review

- **Schema covers the spec data model:** id, title, starts_at, city (brisbane/ipswich check), venue, cost (free/paid), source, url, status (interested/attending/skip), dedup_key (unique), first_seen_run, created_at — all present. ✅
- **NEW detection:** `first_seen_run` + `scrape_runs` table support "NEW = first_seen_run equals latest run id." ✅
- **No placeholders.** ✅
- **Shared contract:** column names here are referenced verbatim by Plan A (writes) and Plan B (reads). ✅

## Handoff

Once all four tasks pass, the schema is live and seeded. Plan A (scraper) and Plan B (dashboard) can both start, using the credentials captured in Task 3.
