import pytest
import aiscraper.config as config_mod
from aiscraper.config import load_config


@pytest.fixture(autouse=True)
def _no_dotenv(monkeypatch):
    # Isolate config tests from any on-disk scraper/.env file.
    monkeypatch.setattr(config_mod, "load_dotenv", lambda *a, **k: None)


def test_load_config_reads_env(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://x.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "secret")
    monkeypatch.setenv("LUMA_CATEGORY_SLUG", "machine-learning")
    cfg = load_config()
    assert cfg.supabase_url == "https://x.supabase.co"
    assert cfg.supabase_key == "secret"
    assert cfg.category_slug == "machine-learning"


def test_load_config_defaults_category_slug_to_ai(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://x.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "secret")
    monkeypatch.delenv("LUMA_CATEGORY_SLUG", raising=False)
    cfg = load_config()
    assert cfg.category_slug == "ai"


def test_load_config_missing_required_raises(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    with pytest.raises(ValueError, match="SUPABASE_URL"):
        load_config()
