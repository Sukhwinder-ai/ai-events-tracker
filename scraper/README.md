# AI Events Scraper

Python scraper that fetches AI events from [Luma](https://lu.ma) using
query-time filtering (it only ever asks Luma for AI calendars / AI search
terms, so results are already relevant — no LLM, no API cost), dedups them,
and writes them to Supabase. Designed to run fortnightly via GitHub Actions.

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
- `LUMA_AI_CALENDARS` — comma-separated Luma AI calendar slugs to pull from.
- `LUMA_AI_QUERIES` — comma-separated AI search terms queried against Luma.

## Run once

    python run.py

Prints `Run <id>: found N events, M new.`

## Test

    pytest

## How AI filtering works

We never pull the whole city feed. We query Luma's AI calendars plus AI search
terms, so the results are already AI-relevant. Filtering happens at query time.

## Playwright (optional)

A read-only browser fallback is available only if a JS-rendered source ever
needs it (`pip install -e ".[browser]"`). The guardrail in
`src/aiscraper/playwright_guard.py` enforces a read-only contract: only GET
requests are allowed through — everything else (POST/PUT/DELETE/PATCH and
clicks, fills, forms) is never performed. The scraper only ever reads public
pages; it never acts on them.
