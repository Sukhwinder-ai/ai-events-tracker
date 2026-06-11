"""CLI entry point. Builds the real Luma source + Supabase writer and runs once."""
from supabase import create_client

from aiscraper.config import load_config
from aiscraper.pipeline import run_pipeline
from aiscraper.sources.luma import LumaSource
from aiscraper.writer import SupabaseWriter


def main() -> None:
    cfg = load_config()
    client = create_client(cfg.supabase_url, cfg.supabase_key)
    source = LumaSource(ai_calendars=cfg.ai_calendars, ai_queries=cfg.ai_queries)
    writer = SupabaseWriter(client)
    result = run_pipeline(source, writer, source_name="luma")
    print(
        f"Run {result.run_id}: found {result.found} events, "
        f"{result.new} new."
    )


if __name__ == "__main__":
    main()
