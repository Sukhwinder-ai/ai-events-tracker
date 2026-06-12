from typing import List

from aiscraper.models import RawEvent


class MultiSource:
    """Runs several sources and concatenates their events.

    A failure in one source (network error, layout change) is logged and
    skipped so the others still contribute — the pipeline dedups across all
    of them afterwards via dedup_key.
    """

    def __init__(self, sources: list):
        self.sources = sources

    def fetch(self) -> List[RawEvent]:
        out: List[RawEvent] = []
        for source in self.sources:
            try:
                out.extend(source.fetch())
            except Exception as exc:  # noqa: BLE001 - one source must not sink the run
                print(f"[multi] source {type(source).__name__} failed: {exc}")
        return out
