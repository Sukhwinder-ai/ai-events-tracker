import { fetchEvents } from "@/lib/fetchEvents";
import { markNew } from "@/lib/events";
import Dashboard from "./components/Dashboard";
import BackgroundVideo from "./components/BackgroundVideo";
import { setStatus } from "./actions";

export const revalidate = 3600;

export default async function Home() {
  const { events, latestRun } = await fetchEvents();
  const views = markNew(events, latestRun);

  return (
    <>
      <BackgroundVideo />
      <main style={{ maxWidth: 1180, margin: "0 auto", padding: "28px 24px", position: "relative" }}>
        <Dashboard initialEvents={views} action={setStatus} />
      </main>
    </>
  );
}
