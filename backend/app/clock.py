from datetime import datetime, timezone

def utcnow() -> datetime:
    """Return a naive UTC datetime for compatibility with existing SQL DateTime columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
