import type { EventRow, EventView } from "./types";

/** Returns the url only if it's a safe http(s) link, else "#". Event urls are
 *  scraped from third-party sites, so this blocks javascript:/data: schemes
 *  from ever reaching an anchor's href. */
export function safeHref(url: string | null | undefined): string {
  if (!url) return "#";
  try {
    const parsed = new URL(url.trim());
    return parsed.protocol === "http:" || parsed.protocol === "https:"
      ? url
      : "#";
  } catch {
    return "#";
  }
}

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

export interface FilterOptions {
  city?: "brisbane" | "ipswich" | "all";
  freeOnly?: boolean;
  newOnly?: boolean;
  search?: string;
}

export function filterEvents(events: EventView[], opts: FilterOptions): EventView[] {
  return events.filter((e) => {
    if (opts.city && opts.city !== "all" && e.city !== opts.city) return false;
    if (opts.freeOnly && e.cost !== "free") return false;
    if (opts.newOnly && !e.isNew) return false;
    if (opts.search) {
      const q = opts.search.toLowerCase();
      const hay = `${e.title} ${e.venue ?? ""}`.toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  });
}

/** Keeps events happening today or later, by calendar day in the viewer's
 *  local timezone — so an event earlier today still shows, but yesterday's
 *  are dropped. Undated events are kept (we can't know they've passed). */
export function filterUpcoming(events: EventView[], now: Date = new Date()): EventView[] {
  const startOfToday = new Date(
    now.getFullYear(),
    now.getMonth(),
    now.getDate(),
  ).getTime();
  return events.filter((e) => {
    if (!e.starts_at) return true;
    const d = new Date(e.starts_at);
    const eventDay = new Date(
      d.getFullYear(),
      d.getMonth(),
      d.getDate(),
    ).getTime();
    return eventDay >= startOfToday;
  });
}

export type SortKey = "date" | "newest";

export function sortEvents(events: EventView[], key: SortKey): EventView[] {
  const copy = [...events];
  if (key === "date") {
    copy.sort((a, b) => (a.starts_at ?? "").localeCompare(b.starts_at ?? ""));
  } else {
    copy.sort((a, b) => (b.created_at ?? "").localeCompare(a.created_at ?? ""));
  }
  return copy;
}
