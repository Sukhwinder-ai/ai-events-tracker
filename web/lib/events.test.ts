import { describe, it, expect } from "vitest";
import { markNew, safeHref } from "./events";
import type { EventRow } from "./types";

describe("safeHref", () => {
  it("keeps http and https urls", () => {
    expect(safeHref("https://lu.ma/ai")).toBe("https://lu.ma/ai");
    expect(safeHref("http://meetup.com/x")).toBe("http://meetup.com/x");
  });

  it("rejects javascript: and data: schemes", () => {
    expect(safeHref("javascript:alert(1)")).toBe("#");
    expect(safeHref("JavaScript:alert(1)")).toBe("#");
    expect(safeHref("  javascript:alert(1)")).toBe("#");
    expect(safeHref("data:text/html,<script>alert(1)</script>")).toBe("#");
  });

  it("falls back to # for null, empty, or unparseable urls", () => {
    expect(safeHref(null)).toBe("#");
    expect(safeHref("")).toBe("#");
    expect(safeHref("not a url")).toBe("#");
  });
});

function row(partial: Partial<EventRow>): EventRow {
  return {
    id: "1", title: "t", starts_at: "2026-06-18T18:00:00+10:00",
    city: "brisbane", venue: "v", cost: "free", source: "luma",
    url: "u", status: null, dedup_key: "k", first_seen_run: 5,
    created_at: "2026-06-10T00:00:00Z", ...partial,
  };
}

describe("markNew", () => {
  it("flags events whose first_seen_run equals the latest run", () => {
    const events = [row({ id: "a", first_seen_run: 5 }), row({ id: "b", first_seen_run: 4 })];
    const result = markNew(events, 5);
    expect(result.find((e) => e.id === "a")!.isNew).toBe(true);
    expect(result.find((e) => e.id === "b")!.isNew).toBe(false);
  });

  it("marks nothing new when latestRun is null", () => {
    const result = markNew([row({ first_seen_run: 5 })], null);
    expect(result[0].isNew).toBe(false);
  });
});

import { visibleInTab } from "./events";

describe("visibleInTab", () => {
  it("All shows everything except skipped", () => {
    expect(visibleInTab("all", null)).toBe(true);
    expect(visibleInTab("all", "interested")).toBe(true);
    expect(visibleInTab("all", "attending")).toBe(true);
    expect(visibleInTab("all", "skip")).toBe(false);
  });

  it("specific tabs show only their own status", () => {
    expect(visibleInTab("interested", "interested")).toBe(true);
    expect(visibleInTab("interested", "attending")).toBe(false);
    expect(visibleInTab("skipped", "skip")).toBe(true);
    expect(visibleInTab("skipped", null)).toBe(false);
  });
});

import { filterEvents, sortEvents } from "./events";
import type { EventView } from "./types";

function view(p: Partial<EventView>): EventView {
  return { ...row({}), isNew: false, ...p } as EventView;
}

describe("filterEvents", () => {
  const events = [
    view({ id: "a", city: "brisbane", cost: "free", title: "RAG Night", isNew: true }),
    view({ id: "b", city: "ipswich", cost: "paid", title: "Vision Workshop", isNew: false }),
  ];

  it("filters by city", () => {
    expect(filterEvents(events, { city: "ipswich" }).map((e) => e.id)).toEqual(["b"]);
  });

  it("filters free only", () => {
    expect(filterEvents(events, { freeOnly: true }).map((e) => e.id)).toEqual(["a"]);
  });

  it("filters new only", () => {
    expect(filterEvents(events, { newOnly: true }).map((e) => e.id)).toEqual(["a"]);
  });

  it("searches title case-insensitively", () => {
    expect(filterEvents(events, { search: "rag" }).map((e) => e.id)).toEqual(["a"]);
  });
});

import { filterUpcoming } from "./events";

describe("filterUpcoming", () => {
  const now = new Date("2026-06-13T09:00:00+10:00");
  const events = [
    view({ id: "past", starts_at: "2026-06-11T18:00:00+10:00" }),
    view({ id: "today-earlier", starts_at: "2026-06-13T07:00:00+10:00" }),
    view({ id: "today-later", starts_at: "2026-06-13T20:00:00+10:00" }),
    view({ id: "future", starts_at: "2026-06-20T18:00:00+10:00" }),
  ];

  it("drops events whose date is before today", () => {
    expect(filterUpcoming(events, now).map((e) => e.id)).toEqual([
      "today-earlier",
      "today-later",
      "future",
    ]);
  });

  it("keeps every event that happens today, regardless of time", () => {
    const ids = filterUpcoming(events, now).map((e) => e.id);
    expect(ids).toContain("today-earlier");
    expect(ids).toContain("today-later");
  });

  it("keeps events with no date rather than guessing", () => {
    const undated = [view({ id: "x", starts_at: null })];
    expect(filterUpcoming(undated, now).map((e) => e.id)).toEqual(["x"]);
  });
});

describe("sortEvents", () => {
  const a = view({ id: "a", starts_at: "2026-06-20T00:00:00Z", created_at: "2026-06-01T00:00:00Z" });
  const b = view({ id: "b", starts_at: "2026-06-14T00:00:00Z", created_at: "2026-06-10T00:00:00Z" });

  it("date sorts soonest first", () => {
    expect(sortEvents([a, b], "date").map((e) => e.id)).toEqual(["b", "a"]);
  });

  it("newest sorts by created_at desc", () => {
    expect(sortEvents([a, b], "newest").map((e) => e.id)).toEqual(["b", "a"]);
  });
});
