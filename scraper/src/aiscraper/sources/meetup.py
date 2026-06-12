import json
import re
from dataclasses import dataclass
from typing import List, Optional

import httpx

from aiscraper.models import RawEvent

FIND_URL = "https://www.meetup.com/find/"
_TIMEOUT = 25.0
# Meetup serves the find page only to browser-like clients; a real UA avoids 403s.
_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
_LDJSON_RE = re.compile(
    r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.S
)


@dataclass
class MeetupCity:
    """A city to search Meetup for, by Meetup's own location token."""
    name: str        # 'brisbane' / 'ipswich' — stamped onto each event
    location: str    # Meetup location token, e.g. 'au--Brisbane'


DEFAULT_CITIES = [
    MeetupCity("brisbane", "au--Brisbane"),
    MeetupCity("ipswich", "au--Ipswich"),
]


class MeetupSource:
    """Fetches AI events from Meetup's public find page.

    Meetup is a JS app with no usable public REST API, but it embeds every
    result as a schema.org Event in <script type="application/ld+json">. Those
    blobs are far more stable than the rotating CSS classes, so we parse them.
    Topic + location scoping happen at query-time via keywords + location.
    """

    def __init__(self, cities: List[MeetupCity], keywords: str = "ai"):
        self.cities = cities
        self.keywords = keywords

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
                    resp = client.get(
                        FIND_URL,
                        params={
                            "keywords": self.keywords,
                            "location": city.location,
                            "source": "EVENTS",
                        },
                    )
                    resp.raise_for_status()
                    events.extend(self._parse(resp.text, city.name))
                except httpx.HTTPError as exc:
                    print(f"[meetup] skipping city {city.name!r}: {exc}")
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
        out: List[RawEvent] = []
        for block in _LDJSON_RE.findall(html):
            try:
                data = json.loads(block)
            except json.JSONDecodeError:
                continue
            for obj in data if isinstance(data, list) else [data]:
                if not isinstance(obj, dict):
                    continue
                if "Event" not in str(obj.get("@type", "")):
                    continue
                out.append(
                    RawEvent(
                        title=obj.get("name", ""),
                        starts_at=obj.get("startDate"),
                        location=self._location(obj),
                        url=obj.get("url"),
                        is_free=self._is_free(obj),
                        source="meetup",
                        city=city_name,
                    )
                )
        return out

    @staticmethod
    def _location(obj: dict) -> Optional[str]:
        loc = obj.get("location") or {}
        if isinstance(loc, list):
            loc = loc[0] if loc else {}
        if not isinstance(loc, dict):
            return None
        if loc.get("name"):
            return loc.get("name")
        addr = loc.get("address")
        if isinstance(addr, dict):
            return addr.get("addressLocality")
        return None

    @staticmethod
    def _is_free(obj: dict) -> Optional[bool]:
        offers = obj.get("offers")
        if not offers:
            return None
        if isinstance(offers, list):
            offers = offers[0] if offers else {}
        if not isinstance(offers, dict):
            return None
        price = offers.get("price")
        if price is None:
            return None
        try:
            return float(price) == 0
        except (TypeError, ValueError):
            return None
