import json
import re
from dataclasses import dataclass
from typing import List, Optional

import httpx

from aiscraper.models import RawEvent

_BASE = "https://www.eventbrite.com.au/d/{slug}/{query}/"
_TIMEOUT = 25.0
_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
# JSON has no internal "};" sequence, so the first one terminates the assignment.
_SERVER_DATA_RE = re.compile(r"window\.__SERVER_DATA__\s*=\s*(\{.*?\});", re.S)


@dataclass
class EventbriteCity:
    """A city to browse Eventbrite for, by its location slug."""
    name: str    # 'brisbane' / 'ipswich' — stamped onto each event
    slug: str    # Eventbrite location slug, e.g. 'australia--brisbane'


DEFAULT_CITIES = [
    EventbriteCity("brisbane", "australia--brisbane"),
    EventbriteCity("ipswich", "australia--ipswich"),
]


def city_url(city: EventbriteCity, query: str) -> str:
    return _BASE.format(slug=city.slug, query=query)


class EventbriteSource:
    """Fetches AI events from Eventbrite's public discovery pages.

    Eventbrite retired its public search API, but the discovery page still
    server-renders results into a window.__SERVER_DATA__ JS blob
    (search_data.events.results) — more stable than its obfuscated CSS.
    Topic + location scoping happen at query-time via the URL path.
    """

    def __init__(self, cities: List[EventbriteCity], query: str = "ai"):
        self.cities = cities
        self.query = query

    def fetch(self) -> List[RawEvent]:
        events: List[RawEvent] = []
        headers = {
            "User-Agent": _USER_AGENT,
            "Accept": "text/html",
            "Accept-Language": "en-AU,en;q=0.9",
        }
        with httpx.Client(
            timeout=_TIMEOUT, headers=headers, follow_redirects=True
        ) as client:
            for city in self.cities:
                try:
                    resp = client.get(city_url(city, self.query))
                    resp.raise_for_status()
                    events.extend(self._parse(resp.text, city.name))
                except httpx.HTTPError as exc:
                    print(f"[eventbrite] skipping city {city.name!r}: {exc}")
        return self._dedup_by_url(events)

    @staticmethod
    def _dedup_by_url(events: List[RawEvent]) -> List[RawEvent]:
        seen = set()
        out: List[RawEvent] = []
        for ev in events:
            if ev.url is not None and ev.url in seen:
                continue
            if ev.url is not None:
                seen.add(ev.url)
            out.append(ev)
        return out

    def _parse(self, html: str, city_name: str) -> List[RawEvent]:
        match = _SERVER_DATA_RE.search(html)
        if not match:
            return []
        try:
            data = json.loads(match.group(1))
        except json.JSONDecodeError:
            return []
        results = (
            data.get("search_data", {})
            .get("events", {})
            .get("results", [])
        )
        out: List[RawEvent] = []
        for ev in results:
            if not isinstance(ev, dict):
                continue
            out.append(
                RawEvent(
                    title=ev.get("name", ""),
                    starts_at=self._starts_at(ev),
                    location=self._location(ev),
                    url=ev.get("url"),
                    is_free=ev.get("is_free"),
                    source="eventbrite",
                    city=city_name,
                )
            )
        return out

    @staticmethod
    def _starts_at(ev: dict) -> Optional[str]:
        date = ev.get("start_date")
        if not date:
            return None
        time = ev.get("start_time")
        return f"{date}T{time}:00" if time else date

    @staticmethod
    def _location(ev: dict) -> Optional[str]:
        venue = ev.get("primary_venue") or {}
        if venue.get("name"):
            return venue.get("name")
        addr = venue.get("address")
        if isinstance(addr, dict):
            return addr.get("city")
        return None
