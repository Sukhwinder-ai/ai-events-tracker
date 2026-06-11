import { describe, it, expect } from "vitest";
import { shapeFetch } from "./fetchEvents";

describe("shapeFetch", () => {
  it("returns events and the max first_seen_run as latestRun", () => {
    const rows = [
      { id: "a", first_seen_run: 4 },
      { id: "b", first_seen_run: 7 },
    ] as any;
    const runs = [{ id: 7 }] as any;
    const out = shapeFetch(rows, runs);
    expect(out.events.length).toBe(2);
    expect(out.latestRun).toBe(7);
  });

  it("latestRun is null when there are no runs", () => {
    const out = shapeFetch([] as any, [] as any);
    expect(out.latestRun).toBeNull();
  });
});
