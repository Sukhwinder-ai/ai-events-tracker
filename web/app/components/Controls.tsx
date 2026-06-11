"use client";

import type { Tab, SortKey } from "@/lib/events";

export interface ControlsState {
  city: "all" | "brisbane" | "ipswich";
  freeOnly: boolean;
  newOnly: boolean;
  search: string;
  sort: SortKey;
  tab: Tab;
}

export default function Controls({
  state,
  onChange,
  newCount,
}: {
  state: ControlsState;
  onChange: (next: Partial<ControlsState>) => void;
  newCount: number;
}) {
  return (
    <div>
      {newCount > 0 && (
        <div style={{ marginBottom: 12, color: "var(--green)" }}>
          🟢 {newCount} new events in the latest scrape
        </div>
      )}
      <input
        placeholder="Search events, venues…"
        value={state.search}
        onChange={(e) => onChange({ search: e.target.value })}
      />
      <div>
        {(["all", "brisbane", "ipswich"] as const).map((c) => (
          <button key={c} onClick={() => onChange({ city: c })}
            aria-pressed={state.city === c}>
            {c === "all" ? "All cities" : c[0].toUpperCase() + c.slice(1)}
          </button>
        ))}
        <button aria-pressed={state.newOnly} onClick={() => onChange({ newOnly: !state.newOnly })}>New only</button>
        <button aria-pressed={state.freeOnly} onClick={() => onChange({ freeOnly: !state.freeOnly })}>Free only</button>
        <select value={state.sort} onChange={(e) => onChange({ sort: e.target.value as SortKey })}>
          <option value="date">Date (soonest)</option>
          <option value="newest">Newest first</option>
        </select>
      </div>
      <div>
        {(["all", "interested", "attending", "skipped"] as const).map((t) => (
          <button key={t} aria-pressed={state.tab === t} onClick={() => onChange({ tab: t })}>
            {t[0].toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>
    </div>
  );
}
