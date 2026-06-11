import { describe, it, expect } from "vitest";
import { markNew } from "./events";
import type { EventRow } from "./types";

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
