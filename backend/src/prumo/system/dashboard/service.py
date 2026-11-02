from datetime import timedelta

from sqlalchemy.orm import Session

from prumo.core.modules import ActivityItem, ModuleSummary, PrumoModule, UpcomingItem
from prumo.system.preferences.service import get_preferences, ordered_modules, today_for
from prumo.system.users.models import User

UPCOMING_HORIZON = timedelta(days=60)
UPCOMING_LIMIT = 10
ACTIVITY_LIMIT = 10


def _enabled(session: Session, user: User) -> list[PrumoModule]:
    preferences = get_preferences(session, user.id)
    return [module for module, enabled in ordered_modules(preferences) if enabled]


def build_dashboard(session: Session, user: User) -> list[ModuleSummary]:
    """One summary per enabled module that provides one, in the user's order."""
    return [module.summary(session, user) for module in _enabled(session, user) if module.summary]


def build_upcoming(session: Session, user: User) -> list[UpcomingItem]:
    """Due items of every enabled module up to 60 days ahead (overdue included), by date."""
    limit = today_for(session, user.id) + UPCOMING_HORIZON
    items = [
        item
        for module in _enabled(session, user)
        if module.upcoming
        for item in module.upcoming(session, user)
        if item.on <= limit
    ]
    items.sort(key=lambda item: (item.on, item.module, item.subject))
    return items[:UPCOMING_LIMIT]


def build_activity(session: Session, user: User) -> list[ActivityItem]:
    """Most recent records of every enabled module, newest first."""
    items = [
        item
        for module in _enabled(session, user)
        if module.activity
        for item in module.activity(session, user)
    ]
    items.sort(key=lambda item: item.occurred_at, reverse=True)
    return items[:ACTIVITY_LIMIT]
