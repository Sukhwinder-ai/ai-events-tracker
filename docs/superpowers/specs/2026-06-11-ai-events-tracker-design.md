# AI Events Tracker — Design Spec

**Date:** 2026-06-11
**Status:** Approved
**Type:** Personal / internal tool (not published publicly)

## Purpose

An interactive dashboard tracking AI events across **Brisbane and Ipswich**. One user (a friend) opens it, filters by city/date, searches, and marks events *interested / attending / skip*. A scraper refreshes the data fortnightly. Built by hand in **Next.js + Supabase + Vercel** — coding the dashboard yourself is the point (the learning goal).

## Scope

**In scope (v1):**
- Cities: Brisbane + Ipswich only (Gold Coast dropped)
- One source: **Luma** (lu.ma) — proves the full pipeline end-to-end
- AI filtering at the source / query-time (AI calendars + AI search terms — no post-fetch filtering, no LLM, no API cost)
- Light-themed dashboard with looping background video
- Filter / sort / search (client-side)
- Status marks (interested / attending / skip) persisted to Supabase
- NEW badge for freshly-scraped events
- Fortnightly scrape via GitHub Actions cron

**Later (designed for, not built in v1):**
- Additional sources: Meetup, Eventbrite, Humanitix, University calendars (UQ/QUT/Griffith)
- Widening AI source queries / additional AI calendars if gaps appear
- Auth (single user, so not needed now)

## Architecture

```
[ Fortnightly scraper (GitHub Actions, Python) ]
              |  pulls Luma events, filters to AI, dedups
              v
       [ Supabase / Postgres ]   <- events catalog + status
              |
              v
   [ Next.js app on Vercel ]   -> what the friend opens
      - Server Components fetch the catalog (ISR)
      - Client Components handle filter / sort / search (React state)
      - Server Actions write status changes back to Supabase
```

**The core separation (main learning goal):**

| Data | Nature | How handled |
|---|---|---|
| Events catalog | Same for everyone, changes fortnightly | Server Component fetch + ISR (`revalidate`) |
| Filter / sort / search | Pure UI | Client Component + React state (`useState`) |
| Status marks | Written back, must persist | Server Action → Supabase write, optimistic UI |

## Components

**1. Scraper (Python)**
- Language: Python (`requests`/`httpx`, `beautifulsoup4`; `playwright` only if a source needs a real browser)
- v1: queries Luma's AI calendars + AI search terms (filtered at source — see below), dedups, writes rows to Supabase via REST API
- Tags each row with the scrape run so NEW events can be identified
- Designed so additional source modules can be added one at a time later

**AI filtering happens at the SOURCE (query-time), not after.** Luma lists all event types in Brisbane/Ipswich, but we never pull the whole city feed and filter it down. Instead the scraper queries Luma in an AI-specific way, so what comes back is already relevant:
- **Targeted AI calendars/communities** — subscribe to Luma's curated AI/ML community calendars for the region; every event on them is AI by definition
- **AI search queries** — hit Luma discovery with AI terms (*AI, artificial intelligence, machine learning, ML, LLM, GenAI, generative, neural, deep learning, data science, RAG, agents, prompt*) scoped to Brisbane/Ipswich — the source returns pre-filtered results
- The keyword list is used as **search queries sent TO Luma**, not as a post-fetch filter
- A light local keyword sanity-check remains only as a cheap backstop to drop obvious false positives — no LLM, no API cost
- **Tradeoff:** query-time filtering relies on events being correctly tagged/listed as AI on Luma. An AI event posted with no AI signal (not in an AI calendar, no AI terms) may be missed. Acceptable for v1 — a clean dashboard beats a noisy one. Queries can be widened later if gaps appear.
- **No Anthropic API / Haiku classifier** — query-time filtering removes the need for an LLM classifier entirely, avoiding ongoing API cost.

**Playwright read-only guardrail (strict):** Playwright is a *fallback only* — used solely if a source serves JS-rendered content that plain HTTP can't read (Luma likely won't need it). Whenever it is used, it operates under a strict read-only contract:
- **Allowed:** navigate (`goto`), wait for selectors, read DOM / `textContent` / attributes, screenshot for debugging only
- **Forbidden:** `click`, `fill`, `type`, `press`, form submission, file upload/download, any `evaluate` that mutates page state, login/auth flows, interactive cookie acceptance
- **Network:** GET requests only — non-GET (POST/PUT/DELETE) blocked at the route-interception level; no writes to any site
- **Identity:** no credentials, no logged-in sessions — public unauthenticated pages only
- **Politeness:** respect rate limits, set a clear descriptive User-Agent, honor robots.txt where applicable
- **Principle:** the scraper only ever *reads* public data; it never *acts* on any site

**2. Supabase (Postgres)**
- Holds the events catalog and status marks
- Fortnightly writes keep the free project from auto-pausing

**3. Next.js dashboard (Vercel)**
- Server Component fetches events with ISR
- Client Component handles all filter/sort/search interactivity
- Server Actions handle status writes with optimistic UI
- Auto-deploys from GitHub on every push

## Data Model — `events` table

- `id` (uuid, primary key)
- `title`
- `starts_at` (timestamp)
- `city` (brisbane / ipswich)
- `venue`
- `cost` (free / paid)
- `source` (luma / meetup / etc.)
- `url`
- `status` (null / interested / attending / skip)
- `dedup_key` (title + date + venue — unique constraint to block duplicates)
- `first_seen_run` (identifier/timestamp of the scrape run that first inserted this event — an event is NEW when this equals the latest run)
- `created_at`

## Feature Behavior

### Dashboard views (status tabs)
- **All** → shows every event *except* skipped (null, interested, attending all visible)
- **Interested** → only interested events
- **Attending** → only attending events
- **Skipped** → only skipped events, with an **un-skip** action to return them to the main view

The main dashboard = "events worth considering." Interested/Attending stay in All (still events to act on); only **Skip** removes a card from All.

### Status marks
- Three actions per card: Interested / Attending / Skip
- Pressing **Skip** immediately (optimistically) removes the card from the All view; it moves to the Skipped tab
- Skipped events remain in the database and can be un-skipped
- Writes go through a Server Action to Supabase

### NEW badge
- An event is **NEW** if it was first seen in the most recent fortnightly scrape run
- Shown as a green pulsing badge + green glow border on the card
- A count banner summarizes ("N new events found in the latest scrape")
- A "New only" filter pill shows just the new events
- **NEW clears each fortnight** — when the next scrape runs, only that run's batch is NEW; the prior batch is no longer flagged

### Filter / sort / search (client-side, React state)
- City filter pills: All cities / Brisbane / Ipswich
- "Free only" toggle
- "New only" toggle
- Search box (title, venue, topic)
- Sort dropdown: Date (soonest) / Newest first

## Visual Design

- **Light theme** — soft pastel gradient base (light blue → lavender → mint → peach)
- **Looping background video** — user-supplied clip at `/public/background.mp4`, rendered as an autoplay/muted/loop/playsinline `<video>` with `object-fit: cover`
  - v1 clip: `14740627_2160_3840_30fps.mp4` (vertical 4K, ~51MB) — will be copied into `/public/background.mp4`
  - Note: vertical source is cropped to fill on wide screens; acceptable for ambient background
  - Note: 51MB is heavy; optional compression to ~1080p deferred (not v1-blocking)
- **Frosted glass cards** (`backdrop-filter: blur`) over the moving background for readability
- Event card shows: date chip, title, location/city badge, cost badge (FREE highlighted), source badge, and the three status actions

## Build Order (thin vertical slice first)

1. **Supabase** — create project, create `events` table, grab URL + keys
2. **Scraper v1** — Luma → write one real event into Supabase (proves the pipe)
3. **Next.js scaffold** — `create-next-app`, connect Supabase client, fetch events in a Server Component, render a plain list. **Deploy to Vercel now.**
4. **ISR** — add `export const revalidate` to the events page
5. **Interactivity** — Client Component with city filter, search, sort on React state
6. **Status marks** — wire `status` to a Server Action with optimistic UI; implement Skip-hides-from-All behavior
7. **NEW badge** — surface latest-scrape events; count banner + New-only filter
8. **Visual polish** — light theme, frosted cards, background video loop
9. **Widen** — add remaining sources one at a time (each with its own targeted AI calendars/queries), plus dedup
10. **Schedule** — move scraper to GitHub Actions with fortnightly cron

**Parallel build:** Next.js dashboard and Python scraper are independent enough to build with parallel agents, coordinating on the Supabase schema as the shared contract.

## Environment Variables

- `SUPABASE_URL`
- `SUPABASE_*_KEY` (anon for client reads, service role for scraper writes)
- *(none needed for AI filtering — done at query-time, no LLM API key required)*

## Tech Checklist

- Node.js + Next.js 15 (`create-next-app`)
- Supabase account + project + `@supabase/supabase-js` (+ `@supabase/ssr` for server reads)
- Vercel account connected to GitHub repo (auto-deploy)
- GitHub repo
- Python scraper (`requests`/`httpx`, `beautifulsoup4`; `playwright` only if needed)

## What We're Deliberately Skipping (v1)

- **Auth** — single user; whole app is "the friend's view." Add Supabase Auth later if desired.
- **Haiku / LLM classifier** — dropped entirely. Query-time AI filtering removes the need and avoids ongoing API cost.
- **Multi-source scraping** — Luma only first; widen once the loop is proven and tested.
- **Video compression** — deferred; revisit if load is slow.
