import httpx
import respx
from aiscraper.sources.luma import LumaSource, CALENDAR_URL


@respx.mock
def test_fetch_calendar_parses_entries():
    payload = {
        "entries": [
            {
                "event": {
                    "name": "Brisbane AI Builders",
                    "start_at": "2026-06-14T18:00:00+10:00",
                    "geo_address_info": {"city_state": "Fortitude Valley, Brisbane"},
                    "url": "brisbane-ai-builders",
                    "ticket_info": {"is_free": True},
                }
            }
        ]
    }
    respx.get(CALENDAR_URL, params={"calendar_api_id": "brisbane-ai"}).mock(
        return_value=httpx.Response(200, json=payload)
    )

    src = LumaSource(ai_calendars=["brisbane-ai"], ai_queries=[])
    raw = src.fetch()

    assert len(raw) == 1
    assert raw[0].title == "Brisbane AI Builders"
    assert raw[0].location == "Fortitude Valley, Brisbane"
    assert raw[0].is_free is True
    assert raw[0].url == "https://lu.ma/brisbane-ai-builders"
    assert raw[0].source == "luma"


@respx.mock
def test_fetch_handles_missing_optional_fields():
    payload = {"entries": [{"event": {"name": "Bare Event"}}]}
    respx.get(CALENDAR_URL, params={"calendar_api_id": "brisbane-ai"}).mock(
        return_value=httpx.Response(200, json=payload)
    )
    src = LumaSource(ai_calendars=["brisbane-ai"], ai_queries=[])
    raw = src.fetch()
    assert raw[0].title == "Bare Event"
    assert raw[0].location is None
    assert raw[0].is_free is None
