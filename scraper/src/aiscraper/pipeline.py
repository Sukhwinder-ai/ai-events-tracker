from aiscraper.dedup import dedup_events
from aiscraper.normalize import to_event


def run_pipeline(source, writer, source_name: str):
    raws = source.fetch()
    events = [ev for ev in (to_event(r) for r in raws) if ev is not None]
    events = dedup_events(events)
    return writer.write_run(source=source_name, events=events)
