import httpx
import respx
from aiscraper.sources.luma import LumaSource, CALENDAR_URL, SEARCH_URL


def _entry(name, slug):
    return {"event": {"name": name, "url": slug}}


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


@respx.mock
def test_fetch_skips_failing_slug_and_returns_others():
    respx.get(CALENDAR_URL, params={"calendar_api_id": "broken"}).mock(
        return_value=httpx.Response(500)
    )
    respx.get(CALENDAR_URL, params={"calendar_api_id": "working"}).mock(
        return_value=httpx.Response(
            200,
            json={"entries": [{"event": {"name": "Good Event", "url": "good"}}]},
        )
    )

    src = LumaSource(ai_calendars=["broken", "working"], ai_queries=[])
    raw = src.fetch()

    assert len(raw) == 1
    assert raw[0].title == "Good Event"


@respx.mock
def test_fetch_queries_search_endpoint_for_each_query():
    respx.get(SEARCH_URL, params={"query": "machine learning"}).mock(
        return_value=httpx.Response(
            200, json={"entries": [_entry("ML Meetup", "ml-meetup")]}
        )
    )

    src = LumaSource(ai_calendars=[], ai_queries=["machine learning"])
    raw = src.fetch()

    assert len(raw) == 1
    assert raw[0].title == "ML Meetup"
    assert raw[0].url == "https://lu.ma/ml-meetup"


@respx.mock
def test_fetch_dedups_calendar_and_query_results_by_url():
    respx.get(CALENDAR_URL, params={"calendar_api_id": "brisbane-ai"}).mock(
        return_value=httpx.Response(
            200, json={"entries": [_entry("Shared Event", "shared")]}
        )
    )
    respx.get(SEARCH_URL, params={"query": "AI"}).mock(
        return_value=httpx.Response(
            200, json={"entries": [_entry("Shared Event", "shared")]}
        )
    )

    src = LumaSource(ai_calendars=["brisbane-ai"], ai_queries=["AI"])
    raw = src.fetch()

    assert len(raw) == 1
    assert raw[0].url == "https://lu.ma/shared"
