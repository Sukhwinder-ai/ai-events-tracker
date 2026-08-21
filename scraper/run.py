"""CLI entry point. Builds every event source + Supabase writer and runs once."""
from supabase import create_client

from aiscraper.config import load_config
from aiscraper.dates import start_of_today
from aiscraper.pipeline import run_pipeline
from aiscraper.sources.luma import LumaSource, DEFAULT_CITIES as LUMA_CITIES
from aiscraper.sources.meetup import (
    MeetupSource,
    DEFAULT_CITIES as MEETUP_CITIES,
)
from aiscraper.sources.multi import MultiSource
from aiscraper.writer import SupabaseWriter


def build_source(slug: str) -> MultiSource:
    """All sources, scoped to the AI topic + Brisbane/Ipswich at query time.

    Eventbrite was removed 2026-08-21. Its CDN (CloudFront) answers 405 to
    every request from GitHub Actions runner IPs (Azure AS8075), so the source
    returned nothing from CI since deployment while succeeding from a local
    AU IP — there is no code-side fix. It was also querying with the Luma
    `ai` slug, which on Eventbrite matched ~1 relevant event in 20. If it is
    ever revived (proxy / self-hosted runner), give it its own query
    (`artificial-intelligence` scored 14/18) rather than reusing the slug.
    """
    return MultiSource(
        [
            LumaSource(cities=LUMA_CITIES, slug=slug),
            MeetupSource(cities=MEETUP_CITIES, keywords=slug),
        ]
    )


def main() -> None:
    cfg = load_config()
    client = create_client(cfg.supabase_url, cfg.supabase_key)
    source = build_source(cfg.category_slug)
    writer = SupabaseWriter(client)
    result = run_pipeline(source, writer, source_name="all")
    print(
        f"Run {result.run_id}: found {result.found} events, "
        f"{result.new} new."
    )

    # Drop events that have already happened (before today, Brisbane time).
    # This is the only delete in the system and is scoped strictly by date.
    removed = writer.purge_past(start_of_today())
    print(f"Purged {removed} past events.")


if __name__ == "__main__":
    main()
