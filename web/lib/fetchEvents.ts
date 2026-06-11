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
