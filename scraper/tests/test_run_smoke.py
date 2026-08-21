import importlib

from aiscraper.config import Config
from aiscraper.sources.luma import LumaSource
from aiscraper.sources.meetup import MeetupSource


def _cfg(luma_slug="ai", meetup_keywords="ai"):
    return Config(
        supabase_url="https://x.supabase.co",
        supabase_key="secret",
        luma_slug=luma_slug,
        meetup_keywords=meetup_keywords,
    )


def test_run_module_exposes_main():
    mod = importlib.import_module("run")
    assert hasattr(mod, "main")


def test_build_source_gives_each_source_its_own_query():
    """Each source must receive its OWN configured query, not a shared one."""
    mod = importlib.import_module("run")
    multi = mod.build_source(_cfg(luma_slug="ai", meetup_keywords="artificial intelligence"))

    by_type = {type(s).__name__: s for s in multi.sources}
    assert isinstance(by_type["LumaSource"], LumaSource)
    assert isinstance(by_type["MeetupSource"], MeetupSource)
    assert by_type["LumaSource"].slug == "ai"
    assert by_type["MeetupSource"].keywords == "artificial intelligence"


def test_tuning_one_source_query_does_not_move_the_other():
    """Regression guard for the coupling this split removed."""
    mod = importlib.import_module("run")
    multi = mod.build_source(_cfg(luma_slug="machine-learning", meetup_keywords="ai"))

    by_type = {type(s).__name__: s for s in multi.sources}
    assert by_type["LumaSource"].slug == "machine-learning"
    assert by_type["MeetupSource"].keywords == "ai"
