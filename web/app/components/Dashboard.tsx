"use client";

import { useState, useMemo } from "react";
import EventCard from "./EventCard";
import Controls, { type ControlsState } from "./Controls";
import { filterEvents, sortEvents, visibleInTab } from "@/lib/events";
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
    setEvents((prev) => prev.map((e) => (e.id === id ? { ...e, status } : e)));
    try {
      await action(id, status);
    } catch {
      setEvents(initialEvents);
    }
  }

  const shown = useMemo(() => {
    const byTab = events.filter((e) => visibleInTab(s.tab, e.status));
    const filtered = filterEvents(byTab, {
      city: s.city, freeOnly: s.freeOnly, newOnly: s.newOnly, search: s.search,
    });
    return sortEvents(filtered, s.sort);
  }, [events, s]);

  return (
    <div>
      <Controls state={s} onChange={update} newCount={newCount} />
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, marginTop: 16 }}>
        {shown.map((e) => (
          <EventCard key={e.id} event={e} onSetStatus={handleSetStatus} />
        ))}
      </div>
    </div>
  );
}
