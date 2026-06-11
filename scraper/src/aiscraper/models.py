from dataclasses import dataclass
from typing import Optional


@dataclass
class RawEvent:
    """Whatever a source hands back, before normalization."""
    title: str
    starts_at: Optional[str]
    location: Optional[str]
    url: Optional[str]
    is_free: Optional[bool]
    source: str


@dataclass
class Event:
    """Matches the Supabase `events` table shape (minus DB-managed fields)."""
    title: str
    starts_at: Optional[str]
    city: str
    venue: Optional[str]
    cost: Optional[str]
    source: str
    url: Optional[str]
    dedup_key: str
    status: Optional[str] = None
