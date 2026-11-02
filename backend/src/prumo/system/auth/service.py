import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import Select, delete, select, update
from sqlalchemy.orm import Session

from prumo.core.clock import utcnow
from prumo.core.config import get_settings
from prumo.core.errors import AuthenticationError, DomainError, NotFoundError, RateLimitedError
from prumo.core.security import (
    DUMMY_PASSWORD_HASH,
    hash_password,
    hash_token,
    new_token,
    password_needs_rehash,
    verify_password,
)
from prumo.system.auth.devices import device_name_from_user_agent
from prumo.system.auth.models import LoginAttempt, SessionClient, UserSession
from prumo.system.users.models import User
from prumo.system.users.service import get_by_username, normalize_username, validate_password

# `last_used_at` is refreshed at most this often, to avoid one write per request.
LAST_USED_RESOLUTION = timedelta(minutes=1)
ATTEMPT_RETENTION = timedelta(days=1)


@dataclass(frozen=True)
class AuthContext:
    user: User
    session: UserSession


@dataclass(frozen=True)
class LoginResult:
    user: User
    session: UserSession
    token: str
    persistent: bool


# ---------------------------------------------------------------- rate limiting


def _locked_for(session: Session, username: str, ip: str, now: datetime) -> int:
    """Seconds left on a lockout for this username and IP, or 0.

    `login_max_failures` failures within `login_window_minutes` (with no success after them) lock
    the pair for `login_lockout_minutes`, counted from the last failure.
    """
    settings = get_settings()
    window = timedelta(minutes=settings.login_window_minutes)
    lockout = timedelta(minutes=settings.login_lockout_minutes)
    last_success = session.scalar(
        select(LoginAttempt.attempted_at)
        .where(
            LoginAttempt.username == username,
            LoginAttempt.ip == ip,
            LoginAttempt.succeeded.is_(True),
        )
        .order_by(LoginAttempt.attempted_at.desc())
        .limit(1)
    )
    since = now - window - lockout
    if last_success is not None and last_success > since:
        since = last_success
    failures = list(
        session.scalars(
            select(LoginAttempt.attempted_at)
            .where(
                LoginAttempt.username == username,
                LoginAttempt.ip == ip,
                LoginAttempt.succeeded.is_(False),
                LoginAttempt.attempted_at > since,
            )
            .order_by(LoginAttempt.attempted_at.desc())
            .limit(settings.login_max_failures)
        )
    )
    if len(failures) < settings.login_max_failures:
        return 0
    newest, oldest = failures[0], failures[-1]
    if newest - oldest > window:
        return 0
    remaining = (newest + lockout - now).total_seconds()
    return max(0, math.ceil(remaining))


def _record_attempt(
    session: Session, username: str, ip: str, *, succeeded: bool, now: datetime
) -> None:
    session.add(LoginAttempt(username=username, ip=ip, succeeded=succeeded, attempted_at=now))
    session.execute(delete(LoginAttempt).where(LoginAttempt.attempted_at < now - ATTEMPT_RETENTION))


# ---------------------------------------------------------------- sessions


def _expiry(client: SessionClient, persistent: bool, now: datetime) -> datetime:
    settings = get_settings()
    if client is SessionClient.APP:
        return now + timedelta(days=settings.session_days_app)
    if persistent:
        return now + timedelta(days=settings.session_days_web)
    return now + timedelta(hours=settings.session_hours_web_transient)


def login(
    session: Session,
    *,
    username: str,
    password: str,
    client: SessionClient,
    device_name: str | None,
    remember: bool,
    ip: str,
    user_agent: str | None,
) -> LoginResult:
    now = utcnow()
    key = normalize_username(username)
    retry_after = _locked_for(session, key, ip, now)
    if retry_after:
        raise RateLimitedError(
            "Too many failed attempts. Try again later.",
            code="auth.rate_limited",
            details={"retry_after_seconds": retry_after},
            headers={"Retry-After": str(retry_after)},
        )

    user = get_by_username(session, key)
    password_ok = verify_password(user.password_hash if user else DUMMY_PASSWORD_HASH, password)
    if user is None or not password_ok:
        _record_attempt(session, key, ip, succeeded=False, now=now)
        session.commit()
        raise AuthenticationError("Invalid username or password.", code="auth.invalid_credentials")

    _record_attempt(session, key, ip, succeeded=True, now=now)
    if password_needs_rehash(user.password_hash):
        user.password_hash = hash_password(password)

    persistent = client is SessionClient.APP or remember
    token = new_token()
    user_session = UserSession(
        user_id=user.id,
        token_hash=hash_token(token),
        client=client,
        device_name=device_name or device_name_from_user_agent(user_agent),
        last_used_at=now,
        expires_at=_expiry(client, persistent, now),
    )
    session.add(user_session)
    session.commit()
    return LoginResult(user=user, session=user_session, token=token, persistent=persistent)


def authenticate(session: Session, token: str) -> AuthContext:
    now = utcnow()
    row = session.execute(
        select(UserSession, User)
        .join(User, User.id == UserSession.user_id)
        .where(UserSession.token_hash == hash_token(token))
    ).one_or_none()
    if row is None:
        raise AuthenticationError()
    user_session, user = row
    if user_session.revoked_at is not None:
        raise AuthenticationError()
    if user_session.expires_at <= now:
        raise AuthenticationError("Session expired.", code="auth.session_expired")
    if now - user_session.last_used_at >= LAST_USED_RESOLUTION:
        user_session.last_used_at = now
        session.commit()
    return AuthContext(user=user, session=user_session)


def _active_sessions_query(user_id: UUID, now: datetime) -> Select[UserSession]:
    return select(UserSession).where(
        UserSession.user_id == user_id,
        UserSession.revoked_at.is_(None),
        UserSession.expires_at > now,
    )


def list_sessions(session: Session, user: User) -> list[UserSession]:
    stmt = _active_sessions_query(user.id, utcnow()).order_by(UserSession.last_used_at.desc())
    return list(session.scalars(stmt))


def revoke_session(session: Session, user: User, session_id: UUID) -> UserSession:
    now = utcnow()
    target = session.scalar(
        _active_sessions_query(user.id, now).where(UserSession.id == session_id)
    )
    if target is None:
        raise NotFoundError()
    target.revoked_at = now
    session.commit()
    return target


def logout(session: Session, current: UserSession) -> None:
    current.revoked_at = utcnow()
    session.commit()


def change_password(
    session: Session, context: AuthContext, *, current_password: str, new_password: str
) -> None:
    """Changes the password and revokes every other session of the user."""
    user = context.user
    if not verify_password(user.password_hash, current_password):
        raise DomainError("Current password is wrong.", code="auth.wrong_password")
    validate_password(new_password)
    user.password_hash = hash_password(new_password)
    now = utcnow()
    session.execute(
        update(UserSession)
        .where(
            UserSession.user_id == user.id,
            UserSession.id != context.session.id,
            UserSession.revoked_at.is_(None),
        )
        .values(revoked_at=now)
    )
    session.commit()
