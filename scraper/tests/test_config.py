import pytest
import aiscraper.config as config_mod
from aiscraper.config import load_config


@pytest.fixture(autouse=True)
def _no_dotenv(monkeypatch):
    # Isolate config tests from any on-disk scraper/.env file.
    monkeypatch.setattr(config_mod, "load_dotenv", lambda *a, **k: None)


@pytest.fixture(autouse=True)
def _supabase_env(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://x.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "secret")


def test_load_config_reads_env(monkeypatch):
    monkeypatch.setenv("LUMA_CATEGORY_SLUG", "machine-learning")
    monkeypatch.setenv("MEETUP_KEYWORDS", "generative ai")
    cfg = load_config()
    assert cfg.supabase_url == "https://x.supabase.co"
    assert cfg.supabase_key == "secret"
    assert cfg.luma_slug == "machine-learning"
    assert cfg.meetup_keywords == "generative ai"


def test_each_source_query_defaults_to_ai(monkeypatch):
    monkeypatch.delenv("LUMA_CATEGORY_SLUG", raising=False)
    monkeypatch.delenv("MEETUP_KEYWORDS", raising=False)
    cfg = load_config()
    assert cfg.luma_slug == "ai"
    assert cfg.meetup_keywords == "ai"


def test_source_queries_are_independent(monkeypatch):
    """The whole point of the split: tuning one source must not move the other.

    Previously a single LUMA_CATEGORY_SLUG drove every source, so a slug good
    for Luma was silently imposed on the rest.
    """
    monkeypatch.setenv("LUMA_CATEGORY_SLUG", "ai")
    monkeypatch.setenv("MEETUP_KEYWORDS", "artificial intelligence")
    cfg = load_config()
    assert cfg.luma_slug == "ai"
    assert cfg.meetup_keywords == "artificial intelligence"


def test_meetup_keywords_does_not_fall_back_to_luma_slug(monkeypatch):
    """Setting only the Luma slug must leave Meetup on its own default."""
    monkeypatch.setenv("LUMA_CATEGORY_SLUG", "machine-learning")
    monkeypatch.delenv("MEETUP_KEYWORDS", raising=False)
    cfg = load_config()
    assert cfg.luma_slug == "machine-learning"
    assert cfg.meetup_keywords == "ai"


def test_load_config_missing_required_raises(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    with pytest.raises(ValueError, match="SUPABASE_URL"):
        load_config()
