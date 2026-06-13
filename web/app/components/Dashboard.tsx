"use client";

import { useState, useMemo } from "react";
import EventCard from "./EventCard";
import Controls, { type ControlsState } from "./Controls";
import { filterEvents, filterUpcoming, sortEvents, visibleInTab } from "@/lib/events";
import type { EventView, StatusValue } from "@/lib/types";

export default function Dashboard({
  initialEvents,
  action,
}: {
  initialEvents: EventView[];
  action: (id: string, status: StatusValue) => Promise<void>;
}) {
  const [events, setEvents] = useState<EventView[]>(initialEvents);
  const [s, setS] = useState<ControlsState>({
    city: "all", freeOnly: false, newOnly: false, search: "", sort: "date", tab: "all",
  });

  const newCount = useMemo(() => events.filter((e) => e.isNew).length, [events]);

  function update(next: Partial<ControlsState>) {
    setS((prev) => ({ ...prev, ...next }));
  }

  async function handleSetStatus(id: string, status: StatusValue) {
    const prevStatus = events.find((e) => e.id === id)?.status ?? null;
    setEvents((prev) => prev.map((e) => (e.id === id ? { ...e, status } : e)));
    try {
      await action(id, status);
    } catch {
      setEvents((prev) => prev.map((e) => (e.id === id ? { ...e, status: prevStatus } : e)));
    }
  }

  const shown = useMemo(() => {
    const upcoming = filterUpcoming(events);
    const byTab = upcoming.filter((e) => visibleInTab(s.tab, e.status));
    const filtered = filterEvents(byTab, {
      city: s.city, freeOnly: s.freeOnly, newOnly: s.newOnly, search: s.search,
    });
    return sortEvents(filtered, s.sort);
  }, [events, s.tab, s.city, s.freeOnly, s.newOnly, s.search, s.sort]);

  return (
    <div>
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          alignItems: "flex-start",
          justifyContent: "space-between",
          gap: 16,
        }}
      >
        <div style={{ flex: "0 0 auto" }}>
          <h1 style={{ fontSize: 24, fontWeight: 800, margin: 0 }}>
            <span style={{ color: "var(--accent)" }}>AI</span> Events Tracker
          </h1>
          <p style={{ color: "var(--muted)", fontSize: 13, margin: "4px 0 0" }}>
            Brisbane &amp; Ipswich · {events.length} events
          </p>
        </div>
        <div style={{ flex: "1 1 480px", minWidth: 0 }}>
          <Controls state={s} onChange={update} newCount={newCount} />
        </div>
      </div>
      <div className="events-grid" style={{ marginTop: 16 }}>
        {shown.map((e) => (
          <EventCard key={e.id} event={e} onSetStatus={handleSetStatus} />
        ))}
      </div>
    </div>
  );
}
