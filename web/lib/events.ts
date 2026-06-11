import type { EventRow, EventView } from "./types";

export function markNew(events: EventRow[], latestRun: number | null): EventView[] {
  return events.map((e) => ({
    ...e,
    isNew: latestRun !== null && e.first_seen_run === latestRun,
  }));
}
