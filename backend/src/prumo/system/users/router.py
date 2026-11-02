from fastapi import APIRouter, status

from prumo.core.deps import SessionDep
from prumo.core.errors import error_responses
from prumo.system.auth import service as auth_service
from prumo.system.auth.deps import CurrentAuth, CurrentUser
from prumo.system.users import service
from prumo.system.users.schemas import PasswordChange, UserRead, UserUpdate

router = APIRouter(tags=["users"], responses=error_responses(401, 403, 422))


@router.get("/me")
def read_me(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)


@router.patch("/me")
def update_me(data: UserUpdate, session: SessionDep, user: CurrentUser) -> UserRead:
    """Updates the display name."""
    return UserRead.model_validate(service.update_profile(session, user, data))


@router.put("/me/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(data: PasswordChange, session: SessionDep, context: CurrentAuth) -> None:
    """Changes the password (requires the current one) and revokes every other session."""
    auth_service.change_password(
        session,
        context,
        current_password=data.current_password,
        new_password=data.new_password,
    )
