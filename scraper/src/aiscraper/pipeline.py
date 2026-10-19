from aiscraper.ai_filter import ai_filter
from aiscraper.dedup import dedup_events
from aiscraper.normalize import to_event


def run_pipeline(source, writer, source_name: str, ai_client=None):
    raws = source.fetch()
    # to_event applies the cheap denylist (relevance.py) and city filter.
    events = [ev for ev in (to_event(r) for r in raws) if ev is not None]
    events = dedup_events(events)
    # Second pass: one Claude call over the deduped titles. Runs after dedup
    # so each title is judged once, and before the write so dropped events
    # never reach the dashboard. Fails open (keeps everything) without a key.
    events, rejected = ai_filter(events, client=ai_client)
    result = writer.write_run(source=source_name, events=events)
    # Events Claude rejected may already be stored from an earlier run (the
    # writer only upserts). Remove them so the dashboard converges on the
    # filter's verdict. `rejected` is empty whenever the filter was skipped.
    writer.remove_keys([e.dedup_key for e in rejected])
    return result
