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
