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
