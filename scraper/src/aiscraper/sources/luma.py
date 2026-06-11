from typing import List, Optional

import httpx

from aiscraper.models import RawEvent

CALENDAR_URL = "https://api.lu.ma/calendar/get-items"
_TIMEOUT = 20.0
_USER_AGENT = "ai-events-tracker/0.1 (personal, read-only)"


class LumaSource:
    """Fetches AI events from Luma using AI-specific calendars and queries.

    Filtering happens here, at query-time: we only ever ask Luma for AI
    calendars / AI search terms, so results are already relevant.
    """

    def __init__(self, ai_calendars: List[str], ai_queries: List[str]):
        self.ai_calendars = ai_calendars
        self.ai_queries = ai_queries

    def fetch(self) -> List[RawEvent]:
        events: List[RawEvent] = []
        headers = {"User-Agent": _USER_AGENT, "Accept": "application/json"}
        with httpx.Client(timeout=_TIMEOUT, headers=headers) as client:
            for slug in self.ai_calendars:
                try:
                    resp = client.get(CALENDAR_URL, params={"calendar_api_id": slug})
                    resp.raise_for_status()
                    events.extend(self._parse(resp.json()))
                except httpx.HTTPError as exc:
                    print(f"[luma] skipping calendar {slug!r}: {exc}")
        return events

    def _parse(self, payload: dict) -> List[RawEvent]:
        out: List[RawEvent] = []
        for entry in payload.get("entries", []):
            ev = entry.get("event", {})
            out.append(
                RawEvent(
                    title=ev.get("name", ""),
                    starts_at=ev.get("start_at"),
                    location=self._location(ev),
                    url=self._url(ev.get("url")),
                    is_free=self._is_free(ev),
                    source="luma",
                )
            )
        return out

    @staticmethod
    def _location(ev: dict) -> Optional[str]:
        geo = ev.get("geo_address_info") or {}
        return geo.get("city_state")

    @staticmethod
    def _url(slug: Optional[str]) -> Optional[str]:
        return f"https://lu.ma/{slug}" if slug else None

    @staticmethod
    def _is_free(ev: dict) -> Optional[bool]:
        ticket = ev.get("ticket_info")
        if not ticket:
            return None
        return ticket.get("is_free")
