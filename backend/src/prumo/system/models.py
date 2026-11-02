"""Imports every platform model so that Alembic sees the full metadata."""

from prumo.system.auth.models import LoginAttempt, UserSession
from prumo.system.preferences.models import UserPreferences
from prumo.system.users.models import User

__all__ = ["LoginAttempt", "User", "UserPreferences", "UserSession"]
