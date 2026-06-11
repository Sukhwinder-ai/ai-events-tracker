import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import Dashboard from "./Dashboard";
import type { EventView } from "@/lib/types";

function view(p: Partial<EventView>): EventView {
  return {
    id: "1", title: "RAG Night", starts_at: "2026-06-14T18:00:00+10:00",
    city: "brisbane", venue: "Valley", cost: "free", source: "luma",
    url: "u", status: null, dedup_key: "k", first_seen_run: 5,
    created_at: "2026-06-10T00:00:00Z", isNew: true, ...p,
  };
}

describe("Dashboard", () => {
  it("hides an event from All immediately when Skip is clicked (optimistic)", async () => {
    const events = [view({ id: "1", title: "RAG Night" })];
    render(<Dashboard initialEvents={events} action={vi.fn().mockResolvedValue(undefined)} />);
    expect(screen.getByText("RAG Night")).toBeDefined();
    fireEvent.click(screen.getByText(/✕ Skip/));
    expect(screen.queryByText("RAG Night")).toBeNull();
  });

  it("filters to Ipswich when the Ipswich pill is clicked", () => {
    const events = [
      view({ id: "1", title: "Bris Event", city: "brisbane" }),
      view({ id: "2", title: "Ips Event", city: "ipswich" }),
    ];
    render(<Dashboard initialEvents={events} action={vi.fn()} />);
    fireEvent.click(screen.getByText("Ipswich"));
    expect(screen.queryByText("Bris Event")).toBeNull();
    expect(screen.getByText("Ips Event")).toBeDefined();
  });
});
