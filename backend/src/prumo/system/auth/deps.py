"""Authentication dependencies, shared by the platform and the modules.

A request authenticates with `Authorization: Bearer <token>` (app) or with the `prumo_session`
cookie (web). With the cookie, requests that change data must also send `X-Prumo-Client: web`
(CSRF defense: a cross-site form cannot set custom headers).
"""

from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import APIKeyCookie, HTTPAuthorizationCredentials, HTTPBearer

from prumo.core.deps import SessionDep
from prumo.core.errors import AuthenticationError, ForbiddenError
from prumo.system.auth import service
from prumo.system.auth.service import AuthContext
from prumo.system.users.models import User

COOKIE_NAME = "prumo_session"
CLIENT_HEADER = "X-Prumo-Client"
SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})

_bearer = HTTPBearer(auto_error=False, description="Session token returned by login (app).")
_cookie = APIKeyCookie(
    name=COOKIE_NAME, auto_error=False, description="Session cookie set by login (web)."
)


def get_auth_context(
    request: Request,
    session: SessionDep,
    bearer: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    cookie: Annotated[str | None, Depends(_cookie)],
) -> AuthContext:
    if bearer is not None:
        return service.authenticate(session, bearer.credentials)
    if cookie is None:
        raise AuthenticationError()
    if request.method not in SAFE_METHODS and request.headers.get(CLIENT_HEADER) != "web":
        raise ForbiddenError(
            f"Cookie-authenticated requests that change data must send {CLIENT_HEADER}: web.",
            code="auth.client_header_required",
        )
    return service.authenticate(session, cookie)


CurrentAuth = Annotated[AuthContext, Depends(get_auth_context)]


def get_current_user(context: CurrentAuth) -> User:
    return context.user


CurrentUser = Annotated[User, Depends(get_current_user)]
