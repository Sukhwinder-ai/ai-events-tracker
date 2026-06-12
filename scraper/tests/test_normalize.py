from aiscraper.models import RawEvent
from aiscraper.normalize import detect_city, make_dedup_key, to_event


def test_detect_city_brisbane_and_ipswich():
    assert detect_city("South Brisbane") == "brisbane"
    assert detect_city("Fire Station 101, Ipswich") == "ipswich"


def test_detect_city_returns_none_when_neither():
    assert detect_city("Gold Coast Convention Centre") is None
    assert detect_city(None) is None


def test_make_dedup_key_is_stable_and_slugified():
    key = make_dedup_key("ML  Meetup!", "2026-06-18T18:00:00+10:00", "South Brisbane")
    assert key == "ml-meetup|2026-06-18|south-brisbane"


def test_to_event_maps_free_and_city():
    raw = RawEvent(
        title="ML Meetup",
        starts_at="2026-06-18T18:00:00+10:00",
        location="South Brisbane",
        url="https://lu.ma/ml",
        is_free=True,
        source="luma",
    )
    ev = to_event(raw)
    assert ev.city == "brisbane"
    assert ev.cost == "free"
    assert ev.dedup_key == "ml-meetup|2026-06-18|south-brisbane"


def test_to_event_returns_none_when_city_unknown():
    raw = RawEvent("X", "2026-06-18T18:00:00+10:00", "Sydney", "u", True, "luma")
    assert to_event(raw) is None


def test_to_event_prefers_raw_city_over_location_detection():
    # The discover API tags the queried city explicitly; the location is just a
    # suburb ("Fortitude Valley") with no 'brisbane' substring to detect.
    raw = RawEvent(
        title="AI Builders Night",
        starts_at="2026-06-18T18:00:00+10:00",
        location="Fortitude Valley",
        url="https://lu.ma/ai",
        is_free=False,
        source="luma",
        city="brisbane",
    )
    ev = to_event(raw)
    assert ev is not None
    assert ev.city == "brisbane"
    assert ev.venue == "Fortitude Valley"
