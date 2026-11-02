from fastapi import APIRouter

from prumo.core.deps import SessionDep
from prumo.core.errors import error_responses
from prumo.system.auth.deps import CurrentUser
from prumo.system.modules.schemas import ModuleList, ModuleRead
from prumo.system.preferences.service import get_preferences, ordered_modules

router = APIRouter(tags=["modules"], responses=error_responses(401))


@router.get("/modules")
def list_modules(session: SessionDep, user: CurrentUser) -> ModuleList:
    """Installed modules in the user's order, with their enabled state."""
    preferences = get_preferences(session, user.id)
    return ModuleList(
        items=[
            ModuleRead(id=module.id, version=module.version, enabled=enabled, position=index)
            for index, (module, enabled) in enumerate(ordered_modules(preferences))
        ]
    )
