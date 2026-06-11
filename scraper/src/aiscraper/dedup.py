from typing import List

from aiscraper.models import Event


def dedup_events(events: List[Event]) -> List[Event]:
    seen = set()
    out = []
    for e in events:
        if e.dedup_key in seen:
            continue
        seen.add(e.dedup_key)
        out.append(e)
    return out
