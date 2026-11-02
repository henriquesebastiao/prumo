from datetime import date, datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from prumo.core.clock import utcnow
from prumo.core.config import get_settings
from prumo.core.modules import PrumoModule, registry
from prumo.system.preferences.models import Theme, UserPreferences
from prumo.system.preferences.schemas import PreferencesUpdate
from prumo.system.users.models import User


def create_default_preferences(session: Session, user: User) -> UserPreferences:
    settings = get_settings()
    preferences = UserPreferences(
        user_id=user.id,
        theme=Theme.SYSTEM,
        locale=settings.default_locale,
        timezone=settings.default_timezone,
        currency=settings.default_currency,
        module_order=list(registry.ids),
        disabled_modules=[],
    )
    session.add(preferences)
    session.flush()
    return preferences


def get_preferences(session: Session, user_id: UUID) -> UserPreferences:
    preferences = session.get(UserPreferences, user_id)
    if preferences is None:
        user = session.get(User, user_id)
        assert user is not None
        preferences = create_default_preferences(session, user)
        session.commit()
    return preferences


def ordered_modules(preferences: UserPreferences) -> list[tuple[PrumoModule, bool]]:
    """Every installed module with its enabled state, in the user's order.

    Modules missing from the stored order (installed after the user last saved) go at the end, in
    installation order, and are enabled.
    """
    position = {module_id: index for index, module_id in enumerate(preferences.module_order)}
    installed = list(registry.modules)
    installed.sort(key=lambda module: position.get(module.id, len(position)))
    disabled = set(preferences.disabled_modules)
    return [(module, module.id not in disabled) for module in installed]


def enabled_module_ids(preferences: UserPreferences) -> list[str]:
    return [module.id for module, enabled in ordered_modules(preferences) if enabled]


def is_module_enabled(session: Session, user_id: UUID, module_id: str) -> bool:
    return module_id in enabled_module_ids(get_preferences(session, user_id))


def update_preferences(session: Session, user: User, data: PreferencesUpdate) -> UserPreferences:
    preferences = get_preferences(session, user.id)
    changes = data.model_dump(exclude_unset=True)
    if "theme" in changes:
        preferences.theme = Theme(changes["theme"])
    for name in ("locale", "timezone", "currency"):
        if name in changes:
            setattr(preferences, name, changes[name])
    if data.enabled_modules is not None:
        enabled = data.enabled_modules
        previous = [module.id for module, _ in ordered_modules(preferences)]
        preferences.module_order = enabled + [m for m in previous if m not in enabled]
        preferences.disabled_modules = [m for m in registry.ids if m not in enabled]
    session.commit()
    return preferences


def timezone_for(session: Session, user_id: UUID) -> ZoneInfo:
    """The user's time zone: "today" and "this month" are computed in it (S3)."""
    return ZoneInfo(get_preferences(session, user_id).timezone)


def now_for(session: Session, user_id: UUID) -> datetime:
    return utcnow().astimezone(timezone_for(session, user_id))


def today_for(session: Session, user_id: UUID) -> date:
    return now_for(session, user_id).date()
