from fastapi import APIRouter

from prumo.core.deps import SessionDep
from prumo.core.errors import error_responses
from prumo.system.auth.deps import CurrentUser
from prumo.system.preferences import service
from prumo.system.preferences.models import UserPreferences
from prumo.system.preferences.schemas import PreferencesRead, PreferencesUpdate

router = APIRouter(tags=["preferences"], responses=error_responses(401, 403, 422))


def _read(preferences: UserPreferences) -> PreferencesRead:
    return PreferencesRead.model_validate(
        {
            "theme": preferences.theme,
            "locale": preferences.locale,
            "timezone": preferences.timezone,
            "currency": preferences.currency,
            "enabled_modules": service.enabled_module_ids(preferences),
            "created_at": preferences.created_at,
            "updated_at": preferences.updated_at,
        }
    )


@router.get("/me/preferences")
def read_preferences(session: SessionDep, user: CurrentUser) -> PreferencesRead:
    return _read(service.get_preferences(session, user.id))


@router.patch("/me/preferences")
def update_preferences(
    data: PreferencesUpdate, session: SessionDep, user: CurrentUser
) -> PreferencesRead:
    return _read(service.update_preferences(session, user, data))
