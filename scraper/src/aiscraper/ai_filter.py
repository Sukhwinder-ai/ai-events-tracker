"""Second-pass relevance filter: Claude reads the surviving titles once per run.

The denylist in relevance.py is cheap and catches the obvious wellness spam,
but the sources' loose keyword matching still lets through things like
"Pencil Figure Sketching" or "NLP Practitioner" (neuro-linguistic programming,
not language models). This step sends ALL remaining titles to Claude in ONE
request and keeps only the ones a Brisbane AI / tech / startup team would
plausibly want to attend.

Design rules:
- One API call per run, never one per event. ~30-60 titles every 3 days.
- Fail OPEN. No API key, a network error, a refusal, or a malformed answer
  means every event is kept and a line is printed. A broken filter must never
  empty the dashboard; the denylist still ran before this.
- Titles only. No URLs or descriptions are sent, so scraped page content
  can't smuggle instructions into the prompt; the model only ever sees a
  numbered list of short strings and answers with booleans.
"""
import os
from typing import List, Optional, Sequence, Tuple

from pydantic import BaseModel, Field

from aiscraper.models import Event

MODEL = "claude-sonnet-5-5"

# More than this share rejected in one run is treated as a bad answer, not a
# verdict: `rejected` drives deletions, and an over-eager model must not be able
# to wipe the dashboard. (Opus rejected ~19% of a real run; Haiku 4.5 rejected
# ~37% and dropped genuine AI events, which is why it is not used.)
MAX_REJECT_SHARE = 0.30

_SYSTEM = (
    "You screen event titles for a small Brisbane AI consultancy whose team "
    "attends local events to meet other people working with AI, software, "
    "startups and data. Keep an event if someone on that team would plausibly "
    "go to it for that reason: AI, machine learning, LLMs, agents, developer "
    "tools, cloud, data, cybersecurity, product, startups, tech founders, "
    "tech community meetups, hackathons, and AI-in-industry talks (AI in "
    "governance, health, property, law, etc.). Drop events that only share a "
    "word with those topics: art and drawing classes, 'NLP' meaning "
    "neuro-linguistic programming, memory or mindset courses, self-help, "
    "fitness, social or language-exchange meetups, generic business "
    "networking with no tech angle. When a title is genuinely ambiguous, keep "
    "it: the cost of a wrong keep is one extra card on a dashboard."
)


class Verdicts(BaseModel):
    keep: List[bool] = Field(
        description="One boolean per numbered title, in the same order."
    )


def _prompt(titles: Sequence[str]) -> str:
    lines = "\n".join(f"{i + 1}. {t}" for i, t in enumerate(titles))
    return (
        f"There are {len(titles)} titles. Return exactly {len(titles)} "
        "booleans, one per title, in order.\n\n" + lines
    )


def classify_titles(titles: Sequence[str], client=None) -> Optional[List[bool]]:
    """Return a keep/drop list aligned with `titles`, or None to mean
    'no verdict, keep everything' (no key, API error, refusal, bad shape)."""
    if not titles:
        return []
    if client is None:
        if not os.getenv("ANTHROPIC_API_KEY"):
            print("AI filter skipped: ANTHROPIC_API_KEY not set.")
            return None
        import anthropic  # imported lazily so tests never need the package

        client = anthropic.Anthropic()
    try:
        response = client.messages.parse(
            model=MODEL,
            max_tokens=4000,
            system=_SYSTEM,
            output_config={"effort": "low"},
            messages=[{"role": "user", "content": _prompt(titles)}],
            output_format=Verdicts,
        )
    except Exception as exc:  # fail open on anything: network, 4xx, 5xx
        print(f"AI filter skipped: {type(exc).__name__}: {exc}")
        return None
    if getattr(response, "stop_reason", None) == "refusal":
        print("AI filter skipped: model refused.")
        return None
    parsed = getattr(response, "parsed_output", None)
    if parsed is None or len(parsed.keep) != len(titles):
        got = None if parsed is None else len(parsed.keep)
        print(f"AI filter skipped: expected {len(titles)} verdicts, got {got}.")
        return None
    return list(parsed.keep)


def ai_filter(events: List[Event], client=None) -> Tuple[List[Event], List[Event]]:
    """Return (kept, rejected). Keeps everything, rejects nothing, on any failure.

    Two fail-open cases beyond a missing verdict: an all-False answer is treated
    as a bad answer rather than "nothing here is relevant", because `rejected`
    drives deletions in the database (see SupabaseWriter.remove_keys).
    """
    verdicts = classify_titles([e.title for e in events], client=client)
    if verdicts is None:
        return events, []
    if events and not any(verdicts):
        print("AI filter skipped: rejected every event, treating as a bad answer.")
        return events, []
    kept = [e for e, keep in zip(events, verdicts) if keep]
    rejected = [e for e, keep in zip(events, verdicts) if not keep]
    if len(events) >= 10 and len(rejected) / len(events) > MAX_REJECT_SHARE:
        print(f"AI filter skipped: wanted to drop {len(rejected)} of "
              f"{len(events)} events (over {MAX_REJECT_SHARE:.0%}), treating as a bad answer: "
              + " | ".join(e.title for e in rejected))
        return events, []
    if rejected:
        print(f"AI filter dropped {len(rejected)}: "
              + " | ".join(e.title for e in rejected))
    return kept, rejected
