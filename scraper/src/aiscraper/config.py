import os
from dataclasses import dataclass
from typing import List

from dotenv import load_dotenv


@dataclass
class Config:
    supabase_url: str
    supabase_key: str
    ai_queries: List[str]
    ai_calendars: List[str]


def _split(value: str) -> List[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


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
        ai_queries=_split(os.getenv("LUMA_AI_QUERIES", "")),
        ai_calendars=_split(os.getenv("LUMA_AI_CALENDARS", "")),
    )
