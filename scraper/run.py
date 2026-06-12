"""CLI entry point. Builds every event source + Supabase writer and runs once."""
from supabase import create_client

from aiscraper.config import load_config
from aiscraper.pipeline import run_pipeline
from aiscraper.sources.eventbrite import (
    EventbriteSource,
    DEFAULT_CITIES as EVENTBRITE_CITIES,
)
from aiscraper.sources.luma import LumaSource, DEFAULT_CITIES as LUMA_CITIES
from aiscraper.sources.meetup import (
    MeetupSource,
    DEFAULT_CITIES as MEETUP_CITIES,
)
from aiscraper.sources.multi import MultiSource
from aiscraper.writer import SupabaseWriter


def build_source(slug: str) -> MultiSource:
    """All sources, scoped to the AI topic + Brisbane/Ipswich at query time."""
    return MultiSource(
        [
            LumaSource(cities=LUMA_CITIES, slug=slug),
            MeetupSource(cities=MEETUP_CITIES, keywords=slug),
            EventbriteSource(cities=EVENTBRITE_CITIES, query=slug),
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


if __name__ == "__main__":
    main()
