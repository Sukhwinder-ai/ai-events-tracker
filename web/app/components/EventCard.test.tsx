import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import EventCard from "./EventCard";
import type { EventView } from "@/lib/types";

function view(p: Partial<EventView>): EventView {
  return {
    id: "1", title: "RAG Night", starts_at: "2026-06-14T18:00:00+10:00",
    city: "brisbane", venue: "Fortitude Valley", cost: "free", source: "luma",
    url: "u", status: null, dedup_key: "k", first_seen_run: 5,
    created_at: "2026-06-10T00:00:00Z", isNew: false, ...p,
  };
}

describe("EventCard", () => {
  it("renders title and a NEW badge when isNew", () => {
    render(<EventCard event={view({ isNew: true })} onSetStatus={vi.fn()} />);
    expect(screen.getByText("RAG Night")).toBeDefined();
    expect(screen.getByText("NEW")).toBeDefined();
  });

  it("calls onSetStatus('skip') when Skip is clicked", () => {
    const onSet = vi.fn();
    render(<EventCard event={view({})} onSetStatus={onSet} />);
    fireEvent.click(screen.getByText(/Skip/));
    expect(onSet).toHaveBeenCalledWith("1", "skip");
  });
});
