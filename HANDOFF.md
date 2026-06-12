# Handoff — AI Events Tracker — 2026-06-11

## Goal
A personal/internal dashboard that tracks AI events across **Brisbane and Ipswich** (Gold Coast was explicitly dropped). A Python scraper pulls events from Luma fortnightly into Supabase; a Next.js dashboard reads them, lets the user's friend mark events interested/attending/skip, and flags events that are NEW in the latest scrape. Built with the superpowers workflow (brainstorm → spec → plans → subagent-driven execution).

## Status
**Code complete and merged to `main` (`1ae00f4`). Working tree clean. All 40 tests pass.** Blocked only on user's manual cloud setup (Supabase data + keys, Vercel import) before it can run live. Nothing has been run against a real Supabase yet.

## Done this session
- Built all 3 plans via subagent-driven development (fresh implementer per plan + two-stage spec/quality review each).
- **Plan A (scraper)** finished: 23 tests. Closed 3 review follow-ups — added `scraper/README.md`, wired the previously-unused `ai_queries` into a Luma search call, and made `fetch()` skip a failing calendar slug instead of aborting the whole run.
- **Plan B (dashboard)** finished: 17 tests, clean production build. Closed 3 review items — fixed a real correctness bug (failed status write now reverts ONLY that event, not all session changes), narrowed the `shown` useMemo deps, and resolved a `force-dynamic`+`revalidate` contradiction in favour of true ISR (page is now Static + 1h revalidate, build-safe with no env vars via a try/catch in `fetchEvents`).
- Ran a final cross-cutting review: **READY TO MERGE** — data contract matches column-for-column across schema/scraper/dashboard, anon vs service_role key split is clean, no secrets committed.
- Added `*.egg-info/` to `scraper/.gitignore`.
- Merged `build/initial-implementation` → `main` (no-ff), re-verified tests, deleted the feature branch.

## Where things stand
- **`db/`** — schema is the source of truth, NOT yet applied to a real Supabase project.
- **`scraper/`** — runnable locally once `.env` has real keys. Tests pass against mocks (respx); never hit live Luma/Supabase yet. Luma's search endpoint (`SEARCH_URL`) was implemented against mocked tests — its real response shape is unverified.
- **`web/`** — builds and tests green. Never rendered against real Supabase data; only the seed row (once applied) will show.
- Everything on `main`; no remote/GitHub repo created yet, no Vercel project yet.

## Next steps
1. **Apply the schema**: in the Supabase SQL editor, run `db/schema.sql` then `db/seed.sql`. Verify both tables (`events`, `scrape_runs`) and the one seeded Brisbane event exist.
2. **Wire the scraper**: `cp scraper/.env.example scraper/.env`, fill `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` (and optionally `LUMA_AI_CALENDARS` / `LUMA_AI_QUERIES`). Run a live scrape (see How to run) and confirm rows land in `events`. This is the first real-world test — watch for Luma API/response-shape surprises.
3. **Wire the dashboard**: `cp web/.env.local.example web/.env.local`, fill `NEXT_PUBLIC_SUPABASE_URL` + `NEXT_PUBLIC_SUPABASE_ANON_KEY`. `cd web && npm run dev`, open http://localhost:3000, confirm the seed/scraped events render. Smoke-test: click Skip → event vanishes from All → appears under the Skipped tab.
4. **Deploy**: push `main` to a new GitHub repo. Import into Vercel with **root directory `web`** + the two `NEXT_PUBLIC_` env vars. Add `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` as GitHub Actions secrets so the fortnightly `.github/workflows/scrape.yml` cron can run.
5. **Later expansion** (designed for, not built): add Meetup, Eventbrite, Humanitix, and UQ/QUT/Griffith sources alongside Luma under `scraper/src/aiscraper/sources/`.

## Key decisions & why
- **Query-time AI filtering, NO LLM classifier** — the scraper queries Luma's AI calendars/search terms so results arrive pre-filtered. This deliberately avoids an Anthropic/Haiku API call and its cost. Do not re-introduce a post-fetch keyword/LLM filter.
- **Skip HIDES from the All view** — the friend only wants to see events worth attending. `visibleInTab("all", "skip") === false`; Skipped events live only under the Skipped tab (with un-skip). Interested/Attending stay in All.
- **NEW clears each fortnight** — an event is NEW iff `first_seen_run === max(scrape_runs.id)`. The writer stamps `first_seen_run` only on dedup_keys not already in the DB, so last fortnight's badges self-clear when a new run gets a new id.
- **Scraper re-runs preserve user status** — writer upserts `on_conflict=dedup_key` and deliberately OMITS `status` (and omits `first_seen_run` for already-seen keys) from the payload, so PostgREST leaves those columns untouched. This is intentional, not a bug.
- **Strict read-only Playwright guard** — `playwright_guard.py` aborts every non-GET method; only `read_text` is exposed (no click/fill/form). Keep it read-only.
- **Two cities only** — `city` enum is `brisbane`/`ipswich`. Gold Coast was dropped.
- **Python for the scraper, Next.js 15/App Router for the dashboard**; they share ONLY the Supabase schema as a contract.

## Gotchas / watch out
- **No live verification yet.** All tests use mocks. The first `scraper/.env` run is where real Luma API quirks will surface — especially the Luma **search** endpoint, whose real JSON shape was never confirmed (implemented against mocked respx tests only).
- **service_role key is write-side only.** It belongs in `scraper/.env` and GitHub Actions secrets — NEVER in `web/` or anything browser-reachable. The dashboard uses the anon key.
- **`web/public/background.mp4` is ~51 MB**, committed (under GitHub's 100 MB limit). Came from `/Users/sukh/Downloads/14740627_2160_3840_30fps.mp4`. If you swap clips, replace this file.
- **Fortnightly cron is approximate** — `0 2 1,15 * *` (1st & 15th, ~14–16 day gaps), a GitHub Actions limitation, not true 14-day cadence.
- **Next.js scaffolded as v16.2.9** (newer than expected); the App Router APIs used (`use server`, `revalidatePath`, `revalidate`) are unchanged and build is clean.
- **`fetchEvents` swallows all errors** → empty dashboard on a Supabase outage with no on-screen signal (acceptable for a personal tool; add a console.error if debugging later).
- The repo is a normal git repo on `main`; there is no remote configured.

## Files touched
- `db/schema.sql` — `events` + `scrape_runs` tables, indexes, enums (city/cost/status), unique `dedup_key`
- `db/seed.sql` — one sample Brisbane event for smoke-testing reads
- `db/README.md` — how to apply schema + credential mapping
- `scraper/` — full Python package: `models.py`, `normalize.py`, `dedup.py`, `config.py`, `sources/luma.py`, `writer.py`, `playwright_guard.py`, `pipeline.py`, `run.py`, 9 test files, `pyproject.toml`, `.env.example`, `README.md`
- `.github/workflows/scrape.yml` — fortnightly scrape cron + manual dispatch
- `web/` — Next.js app: `lib/events.ts` (pure markNew/filter/sort/visibleInTab), `lib/types.ts`, `lib/fetchEvents.ts`, `lib/supabase/server.ts`, `app/page.tsx` (Server Component + ISR), `app/actions.ts` (setStatus Server Action), `app/components/{Dashboard,EventCard,BackgroundVideo,Controls}.tsx`, `app/globals.css` (light frosted theme), `public/background.mp4`, 4 test files
- `docs/superpowers/specs/2026-06-11-ai-events-tracker-design.md` — approved spec
- `docs/superpowers/plans/2026-06-11-plan-{0,a,b}-*.md` — the three executed plans

## How to run / test
```bash
# Scraper tests
cd "scraper" && . .venv/bin/activate && pytest -q          # 23 passed

# Live scrape (needs scraper/.env with real keys)
cd "scraper" && . .venv/bin/activate && python run.py

# Dashboard tests + build
cd "web" && npm test          # 17 passed
cd "web" && npm run build     # clean; / route = Static, Revalidate 1h

# Dashboard dev server (needs web/.env.local with real keys)
cd "web" && npm run dev       # http://localhost:3000
```
Python venv is `scraper/.venv` (Python 3.12 — 3.11+ required; system 3.9 will NOT work).

## Open questions
- Real Supabase project URL + keys (only the user has these) — needed for every live step.
- Whether the Luma search endpoint's real response matches the mocked shape — verify on first live run.
- Which Luma AI calendars/search terms to actually target (`LUMA_AI_CALENDARS` / `LUMA_AI_QUERIES` in `scraper/.env`).
