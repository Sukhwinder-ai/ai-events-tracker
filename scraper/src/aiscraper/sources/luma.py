from dataclasses import dataclass
from typing import List, Optional

import httpx

from aiscraper.models import RawEvent

DISCOVER_URL = "https://api.luma.com/discover/get-paginated-events"
_PAGINATION_LIMIT = 25
_TIMEOUT = 20.0
_USER_AGENT = "ai-events-tracker/0.1 (personal, read-only)"


@dataclass
class CityQuery:
    """A city to pull AI events for, by geo-coordinates."""
    name: str          # 'brisbane' / 'ipswich' — stamped onto each event
    latitude: float
    longitude: float


# The two cities this tracker covers (Gold Coast was dropped by design).
DEFAULT_CITIES = [
    CityQuery("brisbane", -27.4679, 153.0281),
    CityQuery("ipswich", -27.6171, 152.7609),
]


class LumaSource:
    """Fetches AI events from Luma's public discover API.

    Filtering happens at query-time: each city is queried by its coordinates
    plus the AI category slug, so results are already location- and topic-scoped.
    """

    def __init__(self, cities: List[CityQuery], slug: str = "ai"):
        self.cities = cities
        self.slug = slug

    def fetch(self) -> List[RawEvent]:
        events: List[RawEvent] = []
        headers = {"User-Agent": _USER_AGENT, "Accept": "application/json"}
        with httpx.Client(timeout=_TIMEOUT, headers=headers) as client:
            for city in self.cities:
                try:
                    resp = client.get(
                        DISCOVER_URL,
                        params={
                            "latitude": city.latitude,
                            "longitude": city.longitude,
                            "slug": self.slug,
                            "pagination_limit": _PAGINATION_LIMIT,
                        },
                    )
                    resp.raise_for_status()
                    events.extend(self._parse(resp.json(), city.name))
                except httpx.HTTPError as exc:
                    print(f"[luma] skipping city {city.name!r}: {exc}")
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

    def _parse(self, payload: dict, city_name: str) -> List[RawEvent]:
        out: List[RawEvent] = []
        for entry in payload.get("entries", []):
            ev = entry.get("event", {})
            out.append(
                RawEvent(
                    title=ev.get("name", ""),
                    starts_at=ev.get("start_at"),
                    location=self._location(ev),
                    url=self._url(ev.get("url")),
                    is_free=self._is_free(entry),
                    source="luma",
                    city=city_name,
                )
            )
        return out

    @staticmethod
    def _location(ev: dict) -> Optional[str]:
        geo = ev.get("geo_address_info") or {}
        return geo.get("city")

    @staticmethod
    def _url(slug: Optional[str]) -> Optional[str]:
        return f"https://lu.ma/{slug}" if slug else None

    @staticmethod
    def _is_free(entry: dict) -> Optional[bool]:
        ticket = entry.get("ticket_info")
        if not ticket:
            return None
        return ticket.get("is_free")
