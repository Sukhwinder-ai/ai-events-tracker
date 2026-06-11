from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List

from aiscraper.models import Event


@dataclass
class RunResult:
    run_id: int
    found: int
    new: int


class SupabaseWriter:
    """Writes a scrape run + its events. New events (unseen dedup_keys) get
    first_seen_run stamped with this run's id; existing events keep theirs."""

    def __init__(self, client):
        self.client = client

    def write_run(self, source: str, events: List[Event]) -> RunResult:
        run_id = self._open_run(source)
        existing_keys = self._existing_keys([e.dedup_key for e in events])

        rows = []
        new_count = 0
        for e in events:
            row = {
                "title": e.title,
                "starts_at": e.starts_at,
                "city": e.city,
                "venue": e.venue,
                "cost": e.cost,
                "source": e.source,
                "url": e.url,
                "dedup_key": e.dedup_key,
            }
            if e.dedup_key not in existing_keys:
                row["first_seen_run"] = run_id
                new_count += 1
            rows.append(row)

        if rows:
            self.client.table("events").upsert(
                rows, on_conflict="dedup_key"
            ).execute()

        self._close_run(run_id, found=len(events), new=new_count)
        return RunResult(run_id=run_id, found=len(events), new=new_count)

    def _open_run(self, source: str) -> int:
        resp = self.client.table("scrape_runs").insert({"source": source}).execute()
        return resp.data[0]["id"]

    def _existing_keys(self, keys: List[str]) -> set:
        if not keys:
            return set()
        resp = (
            self.client.table("events")
            .select("dedup_key")
            .in_("dedup_key", keys)
            .execute()
        )
        return {row["dedup_key"] for row in resp.data}

    def _close_run(self, run_id: int, found: int, new: int) -> None:
        self.client.table("scrape_runs").update(
            {
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "events_found": found,
                "events_new": new,
            }
        ).eq("id", run_id).execute()
