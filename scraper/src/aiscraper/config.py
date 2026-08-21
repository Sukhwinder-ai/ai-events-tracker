import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass
class Config:
    """Runtime config. Each source carries its own query.

    Source queries are deliberately NOT shared. They look interchangeable —
    they are all "the AI topic" — but each site interprets them differently,
    so one value tuned for one site silently degrades the others. Eventbrite
    was removed in part for this: it inherited Luma's `ai` slug, which on
    Eventbrite matched roughly 1 relevant event in 20.
    """
    supabase_url: str
    supabase_key: str
    luma_slug: str        # Luma discover category slug
    meetup_keywords: str  # Meetup free-text search keywords


def load_config() -> Config:
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url:
        raise ValueError("SUPABASE_URL is required")
    if not key:
        raise ValueError("SUPABASE_SERVICE_ROLE_KEY is required")
    return Config(
        supabase_url=url,
        supabase_key=key,
        # Each defaults independently. A source must never fall back to
        # another source's query — that coupling is the bug this split fixes.
        luma_slug=os.getenv("LUMA_CATEGORY_SLUG", "ai"),
        meetup_keywords=os.getenv("MEETUP_KEYWORDS", "ai"),
    )
