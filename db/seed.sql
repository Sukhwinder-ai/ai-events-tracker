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
