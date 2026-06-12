"use client";

import type { Tab, SortKey } from "@/lib/events";
import Dropdown from "./Dropdown";
import FilterMenu from "./FilterMenu";

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
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      {newCount > 0 && (
        <div style={{ color: "var(--green)" }}>
          🟢 {newCount} new events in the latest scrape
        </div>
      )}
      <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 8 }}>
        <input
          placeholder="Search events, venues…"
          value={state.search}
          onChange={(e) => onChange({ search: e.target.value })}
          style={{ width: "min(260px, 100%)", padding: "7px 11px" }}
        />
        <Dropdown
          ariaLabel="City"
          value={state.city}
          onChange={(v) => onChange({ city: v as ControlsState["city"] })}
          options={[
            { value: "all", label: "All cities" },
            { value: "brisbane", label: "Brisbane" },
            { value: "ipswich", label: "Ipswich" },
          ]}
        />
        <Dropdown
          ariaLabel="Status"
          value={state.tab}
          onChange={(v) => onChange({ tab: v as Tab })}
          options={[
            { value: "all", label: "All" },
            { value: "interested", label: "Interested" },
            { value: "attending", label: "Attending" },
            { value: "skipped", label: "Skipped" },
          ]}
        />
        <FilterMenu
          ariaLabel="Filters"
          items={[
            { key: "newOnly", label: "New only", active: state.newOnly },
            { key: "freeOnly", label: "Free only", active: state.freeOnly },
          ]}
          onToggle={(key) =>
            onChange({ [key]: !state[key as "newOnly" | "freeOnly"] })
          }
        />
        <Dropdown
          ariaLabel="Sort"
          value={state.sort}
          onChange={(v) => onChange({ sort: v as SortKey })}
          options={[
            { value: "date", label: "Date (soonest)" },
            { value: "newest", label: "Newest first" },
          ]}
        />
      </div>
    </div>
  );
}
