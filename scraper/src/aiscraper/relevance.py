import re
from typing import Optional

# Keep-by-default filter. Our sources are already scoped to an "AI" search, so
# we trust what they return and only strip out the lifestyle/wellness/social
# spam that their loose keyword matching drags in. This favours recall over
# precision: the user would rather see an occasional off-topic event than
# silently miss a real tech/startup/science one that lacks an obvious AI word.
_DENY = [
    # Wellness / self-help spam (often keyword-stuffs "AI" into the title)
    r"breathwork", r"meditation", r"\bmanifest", r"soulmate",
    r"emotionally unavailable", r"\bdating\b", r"energy healing",
    # Social / language-exchange meetups
    r"background social", r"easy english", r"lounge asia",
    # Specific non-tech groups the user flagged as noise
    r"aibconnect",
]

_DENY_RE = re.compile("|".join(_DENY), re.IGNORECASE)


def is_relevant(title: Optional[str]) -> bool:
    """True unless the title is known lifestyle/wellness/social spam.

    Keep-by-default: the sources already search for AI, so anything they return
    is kept unless it matches the denylist. This intentionally errs towards
    keeping events (recall) so genuinely useful tech/startup/science events that
    don't spell out "AI" in the title aren't dropped.
    """
    if not title:
        return False
    return not _DENY_RE.search(title)
