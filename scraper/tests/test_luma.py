import httpx
import respx
from aiscraper.sources.luma import LumaSource, CityQuery, DISCOVER_URL

BRIS = CityQuery("brisbane", -27.4679, 153.0281)
IPSW = CityQuery("ipswich", -27.6171, 152.7609)


def _payload(name, slug, city="Fortitude Valley", is_free=True):
    # Mirrors api.luma.com/discover/get-paginated-events: ticket_info lives at
    # the ENTRY level, geo_address_info.city is a suburb, url is a bare slug.
    return {
        "entries": [
            {
                "event": {
                    "name": name,
                    "start_at": "2026-06-14T18:00:00.000Z",
                    "url": slug,
                    "geo_address_info": {"city": city, "region": "Queensland"},
                },
                "ticket_info": None if is_free is None else {"is_free": is_free},
            }
        ],
        "has_more": False,
        "next_cursor": None,
    }


@respx.mock
def test_fetch_discover_parses_entry_fields():
    respx.get(DISCOVER_URL, params={"slug": "ai", "latitude": "-27.4679"}).mock(
        return_value=httpx.Response(
            200, json=_payload("Brisbane AI Builders", "brisbane-ai-builders")
        )
    )
    src = LumaSource(cities=[BRIS], slug="ai")
    raw = src.fetch()

    assert len(raw) == 1
    assert raw[0].title == "Brisbane AI Builders"
    assert raw[0].starts_at == "2026-06-14T18:00:00.000Z"
    assert raw[0].location == "Fortitude Valley"
    assert raw[0].is_free is True
    assert raw[0].url == "https://lu.ma/brisbane-ai-builders"
    assert raw[0].source == "luma"
    assert raw[0].city == "brisbane"


@respx.mock
def test_fetch_stamps_city_from_query_not_location():
    respx.get(DISCOVER_URL, params={"latitude": "-27.4679"}).mock(
        return_value=httpx.Response(200, json=_payload("Bris Event", "bris"))
    )
    respx.get(DISCOVER_URL, params={"latitude": "-27.6171"}).mock(
        return_value=httpx.Response(
            200, json=_payload("Ips Event", "ips", city="Ipswich")
        )
    )
    src = LumaSource(cities=[BRIS, IPSW], slug="ai")
    raw = src.fetch()

    assert {r.title: r.city for r in raw} == {
        "Bris Event": "brisbane",
        "Ips Event": "ipswich",
    }


@respx.mock
def test_fetch_handles_missing_optional_fields():
    payload = {"entries": [{"event": {"name": "Bare Event"}}]}
    respx.get(DISCOVER_URL).mock(return_value=httpx.Response(200, json=payload))
    src = LumaSource(cities=[BRIS], slug="ai")
    raw = src.fetch()
    assert raw[0].title == "Bare Event"
    assert raw[0].location is None
    assert raw[0].is_free is None
    assert raw[0].url is None


@respx.mock
def test_fetch_skips_failing_city_and_returns_others():
    respx.get(DISCOVER_URL, params={"latitude": "-27.4679"}).mock(
        return_value=httpx.Response(500)
    )
    respx.get(DISCOVER_URL, params={"latitude": "-27.6171"}).mock(
        return_value=httpx.Response(
            200, json=_payload("Good Event", "good", city="Ipswich")
        )
    )
    src = LumaSource(cities=[BRIS, IPSW], slug="ai")
    raw = src.fetch()

    assert len(raw) == 1
    assert raw[0].title == "Good Event"


@respx.mock
def test_fetch_dedups_by_url_across_cities():
    respx.get(DISCOVER_URL, params={"latitude": "-27.4679"}).mock(
        return_value=httpx.Response(200, json=_payload("Shared", "shared"))
    )
    respx.get(DISCOVER_URL, params={"latitude": "-27.6171"}).mock(
        return_value=httpx.Response(
            200, json=_payload("Shared", "shared", city="Ipswich")
        )
    )
    src = LumaSource(cities=[BRIS, IPSW], slug="ai")
    raw = src.fetch()

    assert len(raw) == 1
    assert raw[0].url == "https://lu.ma/shared"
    assert raw[0].city == "brisbane"  # first city queried wins the dedup
