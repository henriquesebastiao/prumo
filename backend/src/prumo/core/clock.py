from datetime import UTC, datetime


def utcnow() -> datetime:
    """Current time, timezone-aware, in UTC. The single source of "now" for the backend."""
    return datetime.now(UTC)
