from sqlalchemy.orm import Session

from prumo.core.modules import ModuleSummary
from prumo.system.preferences.service import get_preferences, ordered_modules
from prumo.system.users.models import User


def build_dashboard(session: Session, user: User) -> list[ModuleSummary]:
    """One summary per enabled module that provides one, in the user's order."""
    preferences = get_preferences(session, user.id)
    return [
        module.summary(session, user)
        for module, enabled in ordered_modules(preferences)
        if enabled and module.summary is not None
    ]
