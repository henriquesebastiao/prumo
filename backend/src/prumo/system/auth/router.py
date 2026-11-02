from uuid import UUID

from fastapi import APIRouter, Request, Response, status

from prumo.core.config import get_settings
from prumo.core.deps import SessionDep
from prumo.core.errors import error_responses
from prumo.system.auth import service
from prumo.system.auth.deps import COOKIE_NAME, CurrentAuth
from prumo.system.auth.models import SessionClient
from prumo.system.auth.schemas import LoginRequest, LoginResponse, SessionList, SessionRead
from prumo.system.users.schemas import UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_cookie(response: Response, result: service.LoginResult) -> None:
    settings = get_settings()
    max_age = settings.session_days_web * 86_400 if result.persistent else None
    response.set_cookie(
        COOKIE_NAME,
        result.token,
        max_age=max_age,
        path="/api",
        secure=settings.cookie_secure,
        httponly=True,
        samesite="lax",
    )


def _clear_cookie(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(
        COOKIE_NAME, path="/api", secure=settings.cookie_secure, httponly=True, samesite="lax"
    )


@router.post("/login", responses=error_responses(401, 422, 429))
def login(
    data: LoginRequest, request: Request, response: Response, session: SessionDep
) -> LoginResponse:
    """Creates a session. Web gets an HttpOnly cookie; the app gets the token in the body."""
    result = service.login(
        session,
        username=data.username,
        password=data.password,
        client=data.client,
        device_name=data.device_name,
        remember=data.remember,
        ip=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent"),
    )
    if data.client is SessionClient.WEB:
        _set_cookie(response, result)
    return LoginResponse(
        user=UserRead.model_validate(result.user),
        expires_at=result.session.expires_at,
        token=result.token if data.client is SessionClient.APP else None,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, responses=error_responses(401, 403))
def logout(context: CurrentAuth, session: SessionDep, response: Response) -> None:
    """Revokes the current session."""
    service.logout(session, context.session)
    _clear_cookie(response)


@router.get("/sessions", responses=error_responses(401))
def list_sessions(context: CurrentAuth, session: SessionDep) -> SessionList:
    """Active sessions of the current user, most recently used first."""
    sessions = service.list_sessions(session, context.user)
    return SessionList(
        items=[
            SessionRead(
                id=item.id,
                client=item.client,
                device_name=item.device_name,
                current=item.id == context.session.id,
                last_used_at=item.last_used_at,
                expires_at=item.expires_at,
                created_at=item.created_at,
                updated_at=item.updated_at,
            )
            for item in sessions
        ]
    )


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=error_responses(401, 403, 404),
)
def revoke_session(
    session_id: UUID, context: CurrentAuth, session: SessionDep, response: Response
) -> None:
    """Revokes one of the current user's sessions (any device)."""
    revoked = service.revoke_session(session, context.user, session_id)
    if revoked.id == context.session.id:
        _clear_cookie(response)
