from datetime import UTC, datetime


def ensure_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def ensure_non_null_utc(dt: datetime | None) -> datetime:
    """Convert to UTC. Raises if dt is None (should never happen for non-nullable columns)."""
    if dt is None:
        raise ValueError("Expected a datetime, got None")
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)
