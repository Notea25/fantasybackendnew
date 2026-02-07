"""Timezone utilities for working with Moscow time (UTC+3)."""

from datetime import datetime, timedelta, timezone

# Moscow timezone (UTC+3)
MOSCOW_TZ = timezone(timedelta(hours=3))


def now_msk() -> datetime:
    """Get current time in Moscow timezone.
    
    Returns:
        Current datetime in Moscow timezone (UTC+3)
    """
    return datetime.now(MOSCOW_TZ)


def to_msk(dt: datetime) -> datetime:
    """Convert datetime to Moscow timezone.
    
    Args:
        dt: Datetime to convert (can be naive or aware)
    
    Returns:
        Datetime in Moscow timezone
    """
    if dt.tzinfo is None:
        # Assume naive datetime is UTC
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(MOSCOW_TZ)
