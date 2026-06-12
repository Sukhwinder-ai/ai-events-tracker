import json

import httpx
import respx

from aiscraper.sources.eventbrite import (
    EventbriteSource,
    EventbriteCity,
    city_url,
)

BRIS = EventbriteCity("brisbane", "australia--brisbane")
IPSW = EventbriteCity("ipswich", "australia--ipswich")


def _page(name, url, start_date="2026-06-16", start_time="15:00",
          is_free=None, venue="Brisbane"):
    # Mirrors eventbrite.com.au/d/<slug>/ai/: results live in a JS-assigned
    # window.__SERVER_DATA__ blob under search_data.events.results.
    server_data = {
        "search_data": {
            "events": {
                "results": [
                    {
                        "name": name,
                        "url": url,
                        "start_date": start_date,
                        "start_time": start_time,
                        "is_free": is_free,
                        "primary_venue": {
                            "name": venue,
                            "address": {"city": venue, "country": "AU"},
                        },
                    }
                ]
            }
        }
    }
    return (
        "<html><body><script>window.__SERVER_DATA__ = "
        f"{json.dumps(server_data)};</script></body></html>"
    )


@respx.mock
def test_fetch_parses_result_fields():
    respx.get(city_url(BRIS, "ai")).mock(
        return_value=httpx.Response(
            200,
            html=_page(
                "AI Agents for Business Professionals | Brisbane",
                "https://www.eventbrite.com.au/e/ai-agents-tickets-1988480482652",
            ),
        )
    )
    raw = EventbriteSource(cities=[BRIS], query="ai").fetch()

    assert len(raw) == 1
    assert raw[0].title == "AI Agents for Business Professionals | Brisbane"
    assert raw[0].starts_at == "2026-06-16T15:00:00"
    assert raw[0].location == "Brisbane"
    assert raw[0].url.endswith("1988480482652")
    assert raw[0].source == "eventbrite"
    assert raw[0].city == "brisbane"
    assert raw[0].is_free is None


@respx.mock
def test_fetch_passes_through_is_free():
    respx.get(city_url(BRIS, "ai")).mock(
        return_value=httpx.Response(
            200, html=_page("Free AI Talk", "https://eb/e/1", is_free=True)
        )
    )
    assert EventbriteSource(cities=[BRIS]).fetch()[0].is_free is True


@respx.mock
def test_fetch_date_only_when_no_start_time():
    respx.get(city_url(BRIS, "ai")).mock(
        return_value=httpx.Response(
            200, html=_page("Daylong", "https://eb/e/2", start_time="")
        )
    )
    assert EventbriteSource(cities=[BRIS]).fetch()[0].starts_at == "2026-06-16"


@respx.mock
def test_fetch_stamps_city_from_query():
    respx.get(city_url(BRIS, "ai")).mock(
        return_value=httpx.Response(200, html=_page("Bris", "https://eb/e/b"))
    )
    respx.get(city_url(IPSW, "ai")).mock(
        return_value=httpx.Response(
            200, html=_page("Ips", "https://eb/e/i", venue="Ipswich")
        )
    )
    raw = EventbriteSource(cities=[BRIS, IPSW]).fetch()
    assert {r.title: r.city for r in raw} == {"Bris": "brisbane", "Ips": "ipswich"}


@respx.mock
def test_fetch_skips_failing_city():
    respx.get(city_url(BRIS, "ai")).mock(return_value=httpx.Response(500))
    respx.get(city_url(IPSW, "ai")).mock(
        return_value=httpx.Response(
            200, html=_page("Good", "https://eb/e/g", venue="Ipswich")
        )
    )
    raw = EventbriteSource(cities=[BRIS, IPSW]).fetch()
    assert [r.title for r in raw] == ["Good"]


@respx.mock
def test_fetch_handles_missing_server_data():
    respx.get(city_url(BRIS, "ai")).mock(
        return_value=httpx.Response(200, html="<html><body>no data</body></html>")
    )
    assert EventbriteSource(cities=[BRIS]).fetch() == []


@respx.mock
def test_fetch_dedups_by_url():
    respx.get(city_url(BRIS, "ai")).mock(
        return_value=httpx.Response(200, html=_page("Shared", "https://eb/e/s"))
    )
    respx.get(city_url(IPSW, "ai")).mock(
        return_value=httpx.Response(
            200, html=_page("Shared", "https://eb/e/s", venue="Ipswich")
        )
    )
    raw = EventbriteSource(cities=[BRIS, IPSW]).fetch()
    assert len(raw) == 1
    assert raw[0].city == "brisbane"
