"use server";

import { revalidatePath } from "next/cache";
import { getServerClient } from "@/lib/supabase/server";
import type { StatusValue } from "@/lib/types";

export async function setStatus(id: string, status: StatusValue): Promise<void> {
  const supabase = getServerClient();
  await supabase.from("events").update({ status }).eq("id", id);
  revalidatePath("/");
}
