"use client";

import { safeHref } from "@/lib/events";
import type { EventView, StatusValue } from "@/lib/types";

function monthDay(iso: string | null): { mon: string; day: string } {
  if (!iso) return { mon: "", day: "" };
  const d = new Date(iso);
  return {
    mon: d.toLocaleString("en-AU", { month: "short" }),
    day: String(d.getDate()),
  };
}

export default function EventCard({
  event,
  onSetStatus,
}: {
  event: EventView;
  onSetStatus: (id: string, status: StatusValue) => void;
}) {
  const { mon, day } = monthDay(event.starts_at);
  const toggle = (next: StatusValue) =>
    onSetStatus(event.id, event.status === next ? null : next);
  return (
    <div className={`card${event.isNew ? " is-new" : ""}`} style={{ position: "relative", padding: 12, display: "flex", flexDirection: "column", gap: 8 }}>
      {event.isNew && <span className="new-badge" style={{ position: "absolute", top: -9, right: 14 }}>NEW</span>}
      <div style={{ display: "flex", gap: 10 }}>
        <div style={{ textAlign: "center", minWidth: 44 }}>
          <div style={{ color: "var(--accent)", fontWeight: 700, fontSize: 11, textTransform: "uppercase" }}>{mon}</div>
          <div style={{ fontWeight: 800, fontSize: 18 }}>{day}</div>
        </div>
        <a href={safeHref(event.url)} target="_blank" rel="noreferrer" style={{ fontWeight: 650, fontSize: 14, lineHeight: 1.3, color: "var(--ink)", textDecoration: "none" }}>
          {event.title}
        </a>
      </div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8, fontSize: 12, color: "var(--muted)" }}>
        <span>📍 {event.venue}, {event.city}</span>
        {event.cost === "free" ? <span style={{ color: "var(--green)" }}>FREE</span> : <span>{event.cost}</span>}
        <span style={{ color: "var(--accent)" }}>{event.source}</span>
      </div>
      <div style={{ display: "flex", gap: 8 }}>
        <button aria-pressed={event.status === "interested"} onClick={() => toggle("interested")}>★ Interested</button>
        <button aria-pressed={event.status === "attending"} onClick={() => toggle("attending")}>✓ Attending</button>
        <button aria-pressed={event.status === "skip"} onClick={() => toggle("skip")}>{event.status === "skip" ? "↩ Unskip" : "✕ Skip"}</button>
      </div>
    </div>
  );
}
