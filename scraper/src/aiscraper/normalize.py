import re
from typing import Optional

from aiscraper.models import Event, RawEvent
from aiscraper.relevance import is_ai_relevant

_CITIES = ("brisbane", "ipswich")


def detect_city(location: Optional[str]) -> Optional[str]:
    if not location:
        return None
    low = location.lower()
    for city in _CITIES:
        if city in low:
            return city
    return None


def _slug(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def make_dedup_key(title: str, starts_at: Optional[str], venue: Optional[str]) -> str:
    date_part = (starts_at or "")[:10]  # YYYY-MM-DD
    return f"{_slug(title)}|{date_part}|{_slug(venue or '')}"


def to_event(raw: RawEvent) -> Optional[Event]:
    city = raw.city or detect_city(raw.location)
    if city is None:
        return None
    if not is_ai_relevant(raw.title):
        return None
    cost = "free" if raw.is_free else "paid"
    return Event(
        title=raw.title,
        starts_at=raw.starts_at,
        city=city,
        venue=raw.location,
        cost=cost,
        source=raw.source,
        url=raw.url,
        dedup_key=make_dedup_key(raw.title, raw.starts_at, raw.location),
    )
