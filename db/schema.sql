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
