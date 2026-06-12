import httpx
import respx

from aiscraper.sources.meetup import MeetupSource, MeetupCity, FIND_URL

BRIS = MeetupCity("brisbane", "au--Brisbane")
IPSW = MeetupCity("ipswich", "au--Ipswich")


def _page(name, url, locality="Brisbane", venue="The Precinct", offers=None):
    # Mirrors meetup.com/find: events are embedded as schema.org JSON-LD,
    # alongside a non-event WebSite block that must be ignored.
    event = {
        "@context": "https://schema.org",
        "@type": "Event",
        "name": name,
        "url": url,
        "startDate": "2026-06-17T07:30:00.000Z",
        "location": {
            "@type": "Place",
            "name": venue,
            "address": {
                "@type": "PostalAddress",
                "addressLocality": locality,
                "addressCountry": "au",
            },
        },
    }
    if offers is not None:
        event["offers"] = offers
    import json

    site = {"@context": "https://schema.org", "@type": "WebSite", "name": "Meetup"}
    return (
        "<html><head>"
        f'<script type="application/ld+json">{json.dumps(site)}</script>'
        f'<script type="application/ld+json">{json.dumps(event)}</script>'
        "</head><body></body></html>"
    )


@respx.mock
def test_fetch_parses_ldjson_event():
    respx.get(FIND_URL, params={"location": "au--Brisbane"}).mock(
        return_value=httpx.Response(
            200,
            html=_page(
                "AI & Society | AI in Healthcare",
                "https://www.meetup.com/ai-and-society-australia/events/314486371/",
            ),
        )
    )
    src = MeetupSource(cities=[BRIS], keywords="ai")
    raw = src.fetch()

    assert len(raw) == 1
    assert raw[0].title == "AI & Society | AI in Healthcare"
    assert raw[0].starts_at == "2026-06-17T07:30:00.000Z"
    assert raw[0].location == "The Precinct"
    assert raw[0].url.endswith("/314486371/")
    assert raw[0].source == "meetup"
    assert raw[0].city == "brisbane"
    assert raw[0].is_free is None


@respx.mock
def test_fetch_ignores_non_event_ldjson():
    respx.get(FIND_URL).mock(
        return_value=httpx.Response(200, html=_page("Real Event", "https://m/e/1/"))
    )
    src = MeetupSource(cities=[BRIS], keywords="ai")
    raw = src.fetch()
    assert [r.title for r in raw] == ["Real Event"]


@respx.mock
def test_fetch_reads_free_from_offers():
    respx.get(FIND_URL).mock(
        return_value=httpx.Response(
            200,
            html=_page("Free One", "https://m/e/2/", offers={"@type": "Offer", "price": "0"}),
        )
    )
    src = MeetupSource(cities=[BRIS], keywords="ai")
    assert src.fetch()[0].is_free is True


@respx.mock
def test_fetch_stamps_city_from_query():
    respx.get(FIND_URL, params={"location": "au--Brisbane"}).mock(
        return_value=httpx.Response(200, html=_page("Bris", "https://m/e/b/"))
    )
    respx.get(FIND_URL, params={"location": "au--Ipswich"}).mock(
        return_value=httpx.Response(
            200, html=_page("Ips", "https://m/e/i/", locality="Ipswich")
        )
    )
    src = MeetupSource(cities=[BRIS, IPSW], keywords="ai")
    raw = src.fetch()
    assert {r.title: r.city for r in raw} == {"Bris": "brisbane", "Ips": "ipswich"}


@respx.mock
def test_fetch_skips_failing_city_and_returns_others():
    respx.get(FIND_URL, params={"location": "au--Brisbane"}).mock(
        return_value=httpx.Response(503)
    )
    respx.get(FIND_URL, params={"location": "au--Ipswich"}).mock(
        return_value=httpx.Response(
            200, html=_page("Good", "https://m/e/g/", locality="Ipswich")
        )
    )
    src = MeetupSource(cities=[BRIS, IPSW], keywords="ai")
    raw = src.fetch()
    assert [r.title for r in raw] == ["Good"]


@respx.mock
def test_fetch_dedups_by_url_across_cities():
    respx.get(FIND_URL, params={"location": "au--Brisbane"}).mock(
        return_value=httpx.Response(200, html=_page("Shared", "https://m/e/s/"))
    )
    respx.get(FIND_URL, params={"location": "au--Ipswich"}).mock(
        return_value=httpx.Response(
            200, html=_page("Shared", "https://m/e/s/", locality="Ipswich")
        )
    )
    src = MeetupSource(cities=[BRIS, IPSW], keywords="ai")
    raw = src.fetch()
    assert len(raw) == 1
    assert raw[0].city == "brisbane"
