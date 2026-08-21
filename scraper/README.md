# AI Events Scraper

Python scraper that fetches AI events from [Luma](https://lu.ma) and
[Meetup](https://www.meetup.com) using query-time filtering (it only ever asks
for AI calendars / AI search terms, so results are already relevant — no LLM,
no API cost), dedups them, and writes them to Supabase. Runs weekly (Mondays)
via GitHub Actions.

An Eventbrite source was removed on 2026-08-21: its CDN returns `405` to every
GitHub Actions runner IP, so it silently contributed nothing from CI. See
`build_source` in `run.py` before considering a revival.

## Setup

    python3.12 -m venv .venv
    . .venv/bin/activate
    pip install -e ".[dev]"

## Configure

    cp .env.example .env

Then edit `.env` and fill in:

- `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` (from the Supabase
  Dashboard -> Project Settings -> API). The service_role key is secret and
  write-only for the scraper — never expose it to a browser.
- `LUMA_CATEGORY_SLUG` — Luma discover *category slug* (defaults to `ai`).
- `MEETUP_KEYWORDS` — Meetup free-text *search keywords* (defaults to `ai`).

  Each source has its own query and they are **not** interchangeable — a Luma
  category slug is not a Meetup search term. Tune them independently; never
  feed one value to both. Brisbane + Ipswich locations are built in.

## Run once

    python run.py

Prints `Run <id>: found N events, M new.`

## Test

    pytest

## How AI filtering works

We never pull the whole city feed. Each source is queried for AI at the source
— Luma by category slug, Meetup by keywords — so results arrive already
AI-relevant. Filtering happens at query time.

Because each site interprets a query differently, the queries are configured
per source. Sharing one value across sources looks harmless and is not: it is
how the removed Eventbrite source ended up matching ~1 relevant event in 20.

## Playwright (optional)

A read-only browser fallback is available only if a JS-rendered source ever
needs it (`pip install -e ".[browser]"`). The guardrail in
`src/aiscraper/playwright_guard.py` enforces a read-only contract: only GET
requests are allowed through — everything else (POST/PUT/DELETE/PATCH and
clicks, fills, forms) is never performed. The scraper only ever reads public
pages; it never acts on them.
