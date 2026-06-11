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
