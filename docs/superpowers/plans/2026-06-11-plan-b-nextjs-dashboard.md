# Plan B — Next.js Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A light-themed Next.js dashboard that reads AI events from Supabase (Server Component + ISR), lets the user filter/sort/search client-side, mark events interested/attending/skip via Server Actions (Skip hides from the main view), flags NEW events from the latest scrape, and plays a looping background video behind frosted-glass cards.

**Architecture:** Next.js 15 App Router. A Server Component fetches events with ISR (`revalidate`). A pure data layer (`lib/events.ts`) holds testable logic for the NEW flag, filtering, sorting, and the All-excludes-skipped rule. A Client Component owns filter/sort/search React state. A Server Action updates `status` in Supabase with optimistic UI. Visuals: light gradient theme, frosted cards, a looping `<video>` from `/public/background.mp4`.

**Tech Stack:** Next.js 15, React 19, TypeScript, `@supabase/supabase-js`, `@supabase/ssr`, Vitest + Testing Library, Vercel.

---

## File Structure

Under `web/`:

- Create: `web/` via `create-next-app` (App Router, TS, Tailwind)
- Create: `web/.env.local.example` — public Supabase URL + anon key
- Create: `web/lib/supabase/server.ts` — server-side Supabase client (reads)
- Create: `web/lib/types.ts` — `EventRow`, `StatusValue`, `LatestRun`
- Create: `web/lib/events.ts` — pure logic: `markNew`, `filterEvents`, `sortEvents`, `visibleInTab`
- Create: `web/lib/events.test.ts` — unit tests for the pure logic
- Create: `web/app/page.tsx` — Server Component: fetch + ISR, render dashboard
- Create: `web/app/actions.ts` — Server Action: `setStatus`
- Create: `web/app/components/Dashboard.tsx` — Client Component: state + layout
- Create: `web/app/components/EventCard.tsx` — single card + status buttons
- Create: `web/app/components/BackgroundVideo.tsx` — looping video layer
- Create: `web/app/components/Controls.tsx` — search/city/free/new/sort controls
- Create: `web/app/globals.css` — light theme + frosted styles
- Create: `web/public/background.mp4` — user-supplied loop (copied in)

The pure logic in `lib/events.ts` is the heavily-tested core; React components stay thin.

---

### Task 1: Scaffold Next.js and verify it runs

**Files:**
- Create: `web/` (generated)

- [ ] **Step 1: Create the app**

Run from the repo root:
```bash
npx create-next-app@latest web --typescript --app --tailwind --eslint --src-dir=false --import-alias "@/*" --no-turbopack
```
Accept defaults for any remaining prompts.

- [ ] **Step 2: Verify dev server boots**

Run: `cd web && npm run dev`
Expected: "Ready" on http://localhost:3000. Open it, see the Next.js starter. Stop with Ctrl-C.

- [ ] **Step 3: Add testing deps**

Run:
```bash
cd web && npm install -D vitest @testing-library/react @testing-library/jest-dom jsdom @vitejs/plugin-react
```

- [ ] **Step 4: Configure Vitest**

Create `web/vitest.config.ts`:

```typescript
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
  },
});
```

Add to `web/package.json` scripts:
```json
"test": "vitest run"
```

- [ ] **Step 5: Commit**

```bash
git add web -- ':!web/node_modules'
git commit -m "chore(web): scaffold Next.js app with Vitest"
```

---

### Task 2: Types and the NEW flag

**Files:**
- Create: `web/lib/types.ts`
- Create: `web/lib/events.ts`
- Test: `web/lib/events.test.ts`

- [ ] **Step 1: Write the failing test**

Create `web/lib/events.test.ts`:

```typescript
import { describe, it, expect } from "vitest";
import { markNew } from "./events";
import type { EventRow } from "./types";

function row(partial: Partial<EventRow>): EventRow {
  return {
    id: "1",
    title: "t",
    starts_at: "2026-06-18T18:00:00+10:00",
    city: "brisbane",
    venue: "v",
    cost: "free",
    source: "luma",
    url: "u",
    status: null,
    dedup_key: "k",
    first_seen_run: 5,
    created_at: "2026-06-10T00:00:00Z",
    ...partial,
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd web && npm test`
Expected: FAIL — cannot find `./events`.

- [ ] **Step 3: Write minimal implementation**

Create `web/lib/types.ts`:

```typescript
export type StatusValue = "interested" | "attending" | "skip" | null;

export interface EventRow {
  id: string;
  title: string;
  starts_at: string | null;
  city: "brisbane" | "ipswich";
  venue: string | null;
  cost: "free" | "paid" | null;
  source: string;
  url: string | null;
  status: StatusValue;
  dedup_key: string;
  first_seen_run: number | null;
  created_at: string;
}

export interface EventView extends EventRow {
  isNew: boolean;
}
```

Create `web/lib/events.ts`:

```typescript
import type { EventRow, EventView } from "./types";

export function markNew(events: EventRow[], latestRun: number | null): EventView[] {
  return events.map((e) => ({
    ...e,
    isNew: latestRun !== null && e.first_seen_run === latestRun,
  }));
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd web && npm test`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add web/lib/types.ts web/lib/events.ts web/lib/events.test.ts
git commit -m "feat(web): EventRow types and markNew flag"
```

---

### Task 3: Tab visibility (All excludes skipped)

**Files:**
- Modify: `web/lib/events.ts`
- Modify: `web/lib/events.test.ts`

- [ ] **Step 1: Add the failing test**

Append to `web/lib/events.test.ts`:

```typescript
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd web && npm test`
Expected: FAIL — `visibleInTab` is not exported.

- [ ] **Step 3: Implement**

Append to `web/lib/events.ts`:

```typescript
import type { StatusValue } from "./types";

export type Tab = "all" | "interested" | "attending" | "skipped";

export function visibleInTab(tab: Tab, status: StatusValue): boolean {
  switch (tab) {
    case "all":
      return status !== "skip";
    case "interested":
      return status === "interested";
    case "attending":
      return status === "attending";
    case "skipped":
      return status === "skip";
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd web && npm test`
Expected: PASS (4 passed total).

- [ ] **Step 5: Commit**

```bash
git add web/lib/events.ts web/lib/events.test.ts
git commit -m "feat(web): tab visibility rule (All excludes skipped)"
```

---

### Task 4: Client-side filter and sort

**Files:**
- Modify: `web/lib/events.ts`
- Modify: `web/lib/events.test.ts`

- [ ] **Step 1: Add the failing test**

Append to `web/lib/events.test.ts`:

```typescript
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd web && npm test`
Expected: FAIL — `filterEvents`/`sortEvents` not exported.

- [ ] **Step 3: Implement**

Append to `web/lib/events.ts`:

```typescript
export interface FilterOptions {
  city?: "brisbane" | "ipswich" | "all";
  freeOnly?: boolean;
  newOnly?: boolean;
  search?: string;
}

export function filterEvents(events: EventView[], opts: FilterOptions): EventView[] {
  return events.filter((e) => {
    if (opts.city && opts.city !== "all" && e.city !== opts.city) return false;
    if (opts.freeOnly && e.cost !== "free") return false;
    if (opts.newOnly && !e.isNew) return false;
    if (opts.search) {
      const q = opts.search.toLowerCase();
      const hay = `${e.title} ${e.venue ?? ""}`.toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  });
}

export type SortKey = "date" | "newest";

export function sortEvents(events: EventView[], key: SortKey): EventView[] {
  const copy = [...events];
  if (key === "date") {
    copy.sort((a, b) => (a.starts_at ?? "").localeCompare(b.starts_at ?? ""));
  } else {
    copy.sort((a, b) => (b.created_at ?? "").localeCompare(a.created_at ?? ""));
  }
  return copy;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd web && npm test`
Expected: PASS (all green).

- [ ] **Step 5: Commit**

```bash
git add web/lib/events.ts web/lib/events.test.ts
git commit -m "feat(web): client-side filter and sort logic"
```

---

### Task 5: Supabase server client and data fetch

**Files:**
- Create: `web/.env.local.example`
- Create: `web/lib/supabase/server.ts`
- Create: `web/lib/fetchEvents.ts`
- Test: `web/lib/fetchEvents.test.ts`

- [ ] **Step 1: Install Supabase libs**

Run: `cd web && npm install @supabase/supabase-js @supabase/ssr`

- [ ] **Step 2: Write .env.local.example**

Create `web/.env.local.example`:

```bash
# Supabase Dashboard -> Project Settings -> API
NEXT_PUBLIC_SUPABASE_URL=https://YOUR_PROJECT.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-public-key
```

- [ ] **Step 3: Write the failing test for fetch shaping**

`fetchEvents` returns events plus the latest run id. We test the shaping logic against a fake client.

Create `web/lib/fetchEvents.test.ts`:

```typescript
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
```

- [ ] **Step 4: Run test to verify it fails**

Run: `cd web && npm test`
Expected: FAIL — cannot find `./fetchEvents`.

- [ ] **Step 5: Implement server client + fetch**

Create `web/lib/supabase/server.ts`:

```typescript
import { createClient } from "@supabase/supabase-js";

export function getServerClient() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL!;
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;
  return createClient(url, key);
}
```

Create `web/lib/fetchEvents.ts`:

```typescript
import { getServerClient } from "./supabase/server";
import type { EventRow } from "./types";

export interface FetchResult {
  events: EventRow[];
  latestRun: number | null;
}

export function shapeFetch(
  rows: EventRow[],
  runs: { id: number }[]
): FetchResult {
  const latestRun = runs.length ? Math.max(...runs.map((r) => r.id)) : null;
  return { events: rows, latestRun };
}

export async function fetchEvents(): Promise<FetchResult> {
  const supabase = getServerClient();
  const [{ data: rows }, { data: runs }] = await Promise.all([
    supabase.from("events").select("*"),
    supabase.from("scrape_runs").select("id").order("id", { ascending: false }).limit(1),
  ]);
  return shapeFetch((rows ?? []) as EventRow[], (runs ?? []) as { id: number }[]);
}
```

- [ ] **Step 6: Run test to verify it passes**

Run: `cd web && npm test`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add web/lib/supabase web/lib/fetchEvents.ts web/lib/fetchEvents.test.ts web/.env.local.example web/package.json web/package-lock.json
git commit -m "feat(web): Supabase server client and event fetch shaping"
```

---

### Task 6: Server Action to set status

**Files:**
- Create: `web/app/actions.ts`

This is server-only I/O (writes `status`, then revalidates). We verify it manually in Task 10; here we just implement it correctly.

- [ ] **Step 1: Write the action**

Create `web/app/actions.ts`:

```typescript
"use server";

import { revalidatePath } from "next/cache";
import { getServerClient } from "@/lib/supabase/server";
import type { StatusValue } from "@/lib/types";

export async function setStatus(id: string, status: StatusValue): Promise<void> {
  const supabase = getServerClient();
  await supabase.from("events").update({ status }).eq("id", id);
  revalidatePath("/");
}
```

- [ ] **Step 2: Typecheck**

Run: `cd web && npx tsc --noEmit`
Expected: no type errors.

- [ ] **Step 3: Commit**

```bash
git add web/app/actions.ts
git commit -m "feat(web): setStatus server action"
```

---

### Task 7: Background video + global light theme

**Files:**
- Create: `web/app/components/BackgroundVideo.tsx`
- Modify: `web/app/globals.css`
- Create: `web/public/background.mp4` (copied from the user's clip)

- [ ] **Step 1: Copy the video into place**

Run from the repo root (the user's clip is at `/Users/sukh/Downloads/14740627_2160_3840_30fps.mp4`):
```bash
mkdir -p web/public && cp "/Users/sukh/Downloads/14740627_2160_3840_30fps.mp4" web/public/background.mp4
```
Expected: `web/public/background.mp4` exists.

- [ ] **Step 2: Write the BackgroundVideo component**

Create `web/app/components/BackgroundVideo.tsx`:

```tsx
export default function BackgroundVideo() {
  return (
    <div className="bg-video-wrap" aria-hidden="true">
      <video
        className="bg-video"
        autoPlay
        muted
        loop
        playsInline
        preload="auto"
      >
        <source src="/background.mp4" type="video/mp4" />
      </video>
      <div className="bg-scrim" />
    </div>
  );
}
```

- [ ] **Step 3: Add theme + frosted styles**

Append to `web/app/globals.css`:

```css
:root {
  --ink: #222838;
  --muted: #62708a;
  --accent: #4f6ef0;
  --green: #2eb67d;
  --card: rgba(255, 255, 255, 0.82);
  --border: rgba(0, 0, 0, 0.06);
}

body {
  color: var(--ink);
  background: linear-gradient(125deg, #eef3ff, #f7f0ff, #eafaf5, #fef6ee);
}

.bg-video-wrap { position: fixed; inset: 0; z-index: -1; overflow: hidden; }
.bg-video { width: 100%; height: 100%; object-fit: cover; }
.bg-scrim { position: absolute; inset: 0; background: rgba(255, 255, 255, 0.55); }

.card {
  background: var(--card);
  backdrop-filter: blur(14px);
  border: 1px solid var(--border);
  border-radius: 14px;
  box-shadow: 0 6px 22px rgba(80, 100, 160, 0.1);
}
.card.is-new {
  border-color: rgba(46, 182, 125, 0.5);
  box-shadow: 0 0 0 1px rgba(46, 182, 125, 0.2), 0 6px 22px rgba(80, 100, 160, 0.1);
}
.new-badge {
  background: var(--green); color: #fff; font-size: 11px; font-weight: 800;
  letter-spacing: 0.5px; padding: 3px 9px; border-radius: 999px;
}
```

- [ ] **Step 4: Verify the video is gitignored-safe (size)**

The 51MB mp4 will be committed. Confirm it is acceptable (personal repo). Run: `ls -lh web/public/background.mp4`. Expected: ~51M. (If you later compress it, replace this file.)

- [ ] **Step 5: Commit**

```bash
git add web/app/components/BackgroundVideo.tsx web/app/globals.css web/public/background.mp4
git commit -m "feat(web): looping background video and light frosted theme"
```

---

### Task 8: EventCard component

**Files:**
- Create: `web/app/components/EventCard.tsx`
- Test: `web/app/components/EventCard.test.tsx`

- [ ] **Step 1: Write the failing test**

Create `web/app/components/EventCard.test.tsx`:

```tsx
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
```

- [ ] **Step 2: Add the jsdom matchers setup**

Create `web/vitest.setup.ts`:

```typescript
import "@testing-library/jest-dom";
```

Update `web/vitest.config.ts` test block to include:
```typescript
    setupFiles: ["./vitest.setup.ts"],
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd web && npm test`
Expected: FAIL — cannot find `./EventCard`.

- [ ] **Step 4: Implement EventCard**

Create `web/app/components/EventCard.tsx`:

```tsx
"use client";

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
  return (
    <div className={`card${event.isNew ? " is-new" : ""}`} style={{ position: "relative", padding: 16, display: "flex", flexDirection: "column", gap: 10 }}>
      {event.isNew && <span className="new-badge" style={{ position: "absolute", top: -9, right: 14 }}>NEW</span>}
      <div style={{ display: "flex", gap: 10 }}>
        <div style={{ textAlign: "center", minWidth: 52 }}>
          <div style={{ color: "var(--accent)", fontWeight: 700, fontSize: 11, textTransform: "uppercase" }}>{mon}</div>
          <div style={{ fontWeight: 800, fontSize: 20 }}>{day}</div>
        </div>
        <a href={event.url ?? "#"} target="_blank" rel="noreferrer" style={{ fontWeight: 650, fontSize: 16, color: "var(--ink)", textDecoration: "none" }}>
          {event.title}
        </a>
      </div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8, fontSize: 12, color: "var(--muted)" }}>
        <span>📍 {event.venue}, {event.city}</span>
        {event.cost === "free" ? <span style={{ color: "var(--green)" }}>FREE</span> : <span>{event.cost}</span>}
        <span style={{ color: "var(--accent)" }}>{event.source}</span>
      </div>
      <div style={{ display: "flex", gap: 8 }}>
        <button onClick={() => onSetStatus(event.id, "interested")}>★ Interested</button>
        <button onClick={() => onSetStatus(event.id, "attending")}>✓ Attending</button>
        <button onClick={() => onSetStatus(event.id, "skip")}>✕ Skip</button>
      </div>
    </div>
  );
}
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd web && npm test`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add web/app/components/EventCard.tsx web/app/components/EventCard.test.tsx web/vitest.setup.ts web/vitest.config.ts
git commit -m "feat(web): EventCard with NEW badge and status buttons"
```

---

### Task 9: Dashboard client component (state + optimistic Skip)

**Files:**
- Create: `web/app/components/Controls.tsx`
- Create: `web/app/components/Dashboard.tsx`
- Test: `web/app/components/Dashboard.test.tsx`

- [ ] **Step 1: Write the failing test**

Create `web/app/components/Dashboard.test.tsx`:

```tsx
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
    fireEvent.click(screen.getByText(/Skip/));
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd web && npm test`
Expected: FAIL — cannot find `./Dashboard`.

- [ ] **Step 3: Implement Controls**

Create `web/app/components/Controls.tsx`:

```tsx
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
```

- [ ] **Step 4: Implement Dashboard**

Create `web/app/components/Dashboard.tsx`:

```tsx
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
    // optimistic: update local state immediately (Skip hides from All)
    setEvents((prev) => prev.map((e) => (e.id === id ? { ...e, status } : e)));
    try {
      await action(id, status);
    } catch {
      // revert on failure
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
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd web && npm test`
Expected: PASS — optimistic Skip hides the card; Ipswich filter works.

- [ ] **Step 6: Commit**

```bash
git add web/app/components/Controls.tsx web/app/components/Dashboard.tsx web/app/components/Dashboard.test.tsx
git commit -m "feat(web): dashboard client state, filters, optimistic skip"
```

---

### Task 10: Wire the page with ISR

**Files:**
- Modify: `web/app/page.tsx`

- [ ] **Step 1: Implement the Server Component page**

Replace `web/app/page.tsx` with:

```tsx
import { fetchEvents } from "@/lib/fetchEvents";
import { markNew } from "@/lib/events";
import Dashboard from "./components/Dashboard";
import BackgroundVideo from "./components/BackgroundVideo";
import { setStatus } from "./actions";

export const revalidate = 3600; // ISR: re-fetch catalog hourly

export default async function Home() {
  const { events, latestRun } = await fetchEvents();
  const views = markNew(events, latestRun);

  return (
    <>
      <BackgroundVideo />
      <main style={{ maxWidth: 1100, margin: "0 auto", padding: "28px 24px", position: "relative" }}>
        <h1 style={{ fontSize: 24, fontWeight: 800 }}>
          <span style={{ color: "var(--accent)" }}>AI</span> Events Tracker
        </h1>
        <p style={{ color: "var(--muted)", fontSize: 13, marginBottom: 20 }}>
          Brisbane &amp; Ipswich · {views.length} events
        </p>
        <Dashboard initialEvents={views} action={setStatus} />
      </main>
    </>
  );
}
```

- [ ] **Step 2: Typecheck and build**

Run: `cd web && npx tsc --noEmit && npm run build`
Expected: type-clean; build succeeds.

- [ ] **Step 3: Local run against real Supabase**

Create `web/.env.local` from the example with your real `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`. Then:
```bash
cd web && npm run dev
```
Expected: http://localhost:3000 shows the seed event (from Plan 0) on the frosted card over the looping video. Click Skip → it disappears from All; open the Skipped tab → it's there.

- [ ] **Step 4: Run full test suite**

Run: `cd web && npm test`
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add web/app/page.tsx
git commit -m "feat(web): wire dashboard page with ISR and Supabase fetch"
```

---

### Task 11: Deploy to Vercel (manual)

**Files:** none

- [ ] **Step 1: Push the repo to GitHub**

Ensure the repo is on GitHub (create it if needed) and pushed.

- [ ] **Step 2: Import into Vercel**

In Vercel: **Add New → Project → import the GitHub repo**. Set the **Root Directory** to `web`. Framework preset: Next.js (auto-detected).

- [ ] **Step 3: Add environment variables in Vercel**

Project → **Settings → Environment Variables**: add `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` (same values as `.env.local`).

- [ ] **Step 4: Deploy and verify**

Trigger the deploy. Expected: build succeeds, the live URL shows the dashboard with the seed event over the video background. Every future `git push` auto-deploys.

---

## Self-Review

- **Spec coverage:** Server Component + ISR fetch (Task 10, `revalidate`), client filter/sort/search (Tasks 4,9), city brisbane/ipswich (Tasks 4,9), Free-only + New-only (Tasks 4,9), search (Task 4), status via Server Action (Task 6), Skip-hides-from-All optimistic (Tasks 3,9), NEW badge + count (Tasks 2,8,9), light theme + frosted cards (Task 7), looping background video from /public/background.mp4 (Task 7), Vercel deploy (Task 11). ✅
- **Type consistency:** `EventRow`/`EventView`/`StatusValue`, `Tab`, `SortKey`, `markNew`, `filterEvents`, `sortEvents`, `visibleInTab`, `setStatus` names match across tasks. ✅
- **No placeholders.** ✅
- **Shared contract:** reads columns (`status`, `first_seen_run`, `city`, `cost`, etc.) matching Plan 0 verbatim; `scrape_runs.id` used for latestRun. ✅
- **Note:** card/control styling is functional inline + globals.css (matches the approved mockups' structure); polish can iterate against the live page. Visual mockups in `.superpowers/brainstorm/` are the reference.

## Handoff

This plan depends on Plan 0 (schema live) and is independent of Plan A — they can run in parallel, sharing only the Supabase schema.
