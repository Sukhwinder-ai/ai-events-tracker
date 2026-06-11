import type { EventRow, EventView } from "./types";

export function markNew(events: EventRow[], latestRun: number | null): EventView[] {
  return events.map((e) => ({
    ...e,
    isNew: latestRun !== null && e.first_seen_run === latestRun,
  }));
}

import type { StatusValue } from "./types";

export type Tab = "all" | "interested" | "attending" | "skipped";

export function visibleInTab(tab: Tab, status: StatusValue): boolean {
  switch (tab) {
    case "all":
      return status !== "skip";
    case "interested":
      return status === "interested";
    case "attending":
      return status === "attending";
    case "skipped":
      return status === "skip";
  }
}
