import pytest
from aiscraper.config import load_config


def test_load_config_reads_env(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://x.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "secret")
    monkeypatch.setenv("LUMA_AI_QUERIES", "AI, machine learning")
    monkeypatch.setenv("LUMA_AI_CALENDARS", "brisbane-ai")
    cfg = load_config()
    assert cfg.supabase_url == "https://x.supabase.co"
    assert cfg.supabase_key == "secret"
    assert cfg.ai_queries == ["AI", "machine learning"]
    assert cfg.ai_calendars == ["brisbane-ai"]


def test_load_config_missing_required_raises(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    with pytest.raises(ValueError, match="SUPABASE_URL"):
        load_config()
