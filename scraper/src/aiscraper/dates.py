from datetime import datetime
from typing import Optional

from zoneinfo import ZoneInfo

# Events are Brisbane/Ipswich (both Australia/Brisbane, UTC+10, no DST). The
# scraper runs in UTC on CI, so "today" must be computed in Brisbane time —
# otherwise a still-current event could be judged "past" near midnight.
BRISBANE = ZoneInfo("Australia/Brisbane")


def start_of_today(now: Optional[datetime] = None) -> str:
    """Midnight at the start of today, in Brisbane time, as an ISO string.

    This is the cut-off for purging: events strictly before it have already
    happened (by calendar day) and are deleted; events at or after it stay.
    """
    if now is None:
        now = datetime.now(BRISBANE)
    local = now.astimezone(BRISBANE)
    midnight = local.replace(hour=0, minute=0, second=0, microsecond=0)
    return midnight.isoformat()
