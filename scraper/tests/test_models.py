from aiscraper.models import RawEvent, Event


def test_rawevent_holds_source_fields():
    raw = RawEvent(
        title="ML Meetup",
        starts_at="2026-06-18T18:00:00+10:00",
        location="South Brisbane",
        url="https://lu.ma/ml",
        is_free=True,
        source="luma",
    )
    assert raw.title == "ML Meetup"
    assert raw.is_free is True


def test_event_is_the_db_shape():
    ev = Event(
        title="ML Meetup",
        starts_at="2026-06-18T18:00:00+10:00",
        city="brisbane",
        venue="South Brisbane",
        cost="free",
        source="luma",
        url="https://lu.ma/ml",
        dedup_key="ml-meetup|2026-06-18|south-brisbane",
    )
    assert ev.city == "brisbane"
    assert ev.cost == "free"
    assert ev.status is None
