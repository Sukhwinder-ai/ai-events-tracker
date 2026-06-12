import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass
class Config:
    supabase_url: str
    supabase_key: str
    category_slug: str


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
        category_slug=os.getenv("LUMA_CATEGORY_SLUG", "ai"),
    )
