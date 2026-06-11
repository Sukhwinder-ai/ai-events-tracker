from aiscraper.models import RawEvent, Event
from aiscraper.pipeline import run_pipeline


class StubSource:
    def __init__(self, raws):
        self._raws = raws

    def fetch(self):
        return self._raws


class StubWriter:
    def __init__(self):
        self.written = None

    def write_run(self, source, events):
        self.written = events
        from aiscraper.writer import RunResult
        new = len(events)
        return RunResult(run_id=1, found=len(events), new=new)


def test_pipeline_normalizes_dedups_and_writes():
    raws = [
        RawEvent("ML Meetup", "2026-06-18T18:00:00+10:00", "South Brisbane",
                 "https://lu.ma/ml", True, "luma"),
        # duplicate of the first after normalization
        RawEvent("ML Meetup", "2026-06-18T18:00:00+10:00", "South Brisbane",
                 "https://lu.ma/ml", True, "luma"),
        # dropped: city not Brisbane/Ipswich
        RawEvent("Sydney AI", "2026-06-18T18:00:00+10:00", "Sydney",
                 "https://lu.ma/syd", True, "luma"),
    ]
    writer = StubWriter()
    result = run_pipeline(StubSource(raws), writer, source_name="luma")

    assert len(writer.written) == 1  # deduped + city-filtered
    assert writer.written[0].city == "brisbane"
    assert result.found == 1
