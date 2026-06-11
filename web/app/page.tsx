import { fetchEvents } from "@/lib/fetchEvents";
import { markNew } from "@/lib/events";
import Dashboard from "./components/Dashboard";
import BackgroundVideo from "./components/BackgroundVideo";
import { setStatus } from "./actions";

export const dynamic = "force-dynamic";
export const revalidate = 3600;

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
