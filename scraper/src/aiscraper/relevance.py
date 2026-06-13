import re
from typing import Optional

# Broad AI/tech allowlist. Meetup/Eventbrite's keyword search is loose and
# returns lifestyle/networking noise, so we keep only events whose title shows
# a real AI signal — or an adjacent tech-community signal AI folks care about.
_ALLOW = [
    # Core AI / ML
    r"\bai\b", r"\bml\b", r"a\.i\.", r"artificial intelligence",
    r"machine learning", r"deep learning", r"neural", r"\bnlp\b",
    r"natural language", r"computer vision", r"\bllms?\b",
    r"large language model", r"\bgpt\b", r"chatgpt", r"generative",
    r"\bgen ?ai\b", r"prompt engineering", r"\brag\b", r"agentic",
    r"\bai agents?\b", r"mlops", r"data science", r"data engineering",
    # Branded AI tools / labs
    r"openai", r"anthropic", r"\bclaude\b", r"\bgemini\b", r"copilot",
    r"perplexity", r"\bllama\b", r"mistral", r"hugging ?face", r"langchain",
    r"stable diffusion", r"midjourney", r"transformers?",
    # Adjacent tech communities (broad mode)
    r"databricks", r"snowflake", r"\baws\b", r"\bazure\b", r"google cloud",
    r"\bgcp\b", r"\bgdg\b", r"google developer", r"microsoft fabric",
    r"kubernetes",
]

# Even with an AI token, these wellness/lifestyle terms mark keyword-stuffed
# spam that isn't really a tech event — drop outright.
_DENY = [
    r"breathwork", r"meditation", r"\bmanifest", r"soulmate",
    r"emotionally unavailable", r"\bdating\b", r"energy healing",
]

_ALLOW_RE = re.compile("|".join(_ALLOW), re.IGNORECASE)
_DENY_RE = re.compile("|".join(_DENY), re.IGNORECASE)


def is_ai_relevant(title: Optional[str]) -> bool:
    """True if the event title signals an AI or adjacent-tech event.

    Loose source searches return lifestyle noise; this keeps the dashboard
    on-topic. A small denylist removes wellness spam that stuffs 'AI' into
    otherwise-unrelated titles.
    """
    if not title:
        return False
    if _DENY_RE.search(title):
        return False
    return bool(_ALLOW_RE.search(title))
