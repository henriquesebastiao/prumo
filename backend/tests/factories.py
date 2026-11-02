"""Plain functions that create records with sensible defaults."""

from datetime import timedelta

from sqlalchemy.orm import Session

from prumo.core.clock import utcnow
from prumo.core.security import hash_token, new_token
from prumo.system.auth.models import SessionClient, UserSession
from prumo.system.users.models import User
from prumo.system.users.service import create_user as service_create_user

DEFAULT_PASSWORD = "senha-segura-123"


def create_user(
    db: Session,
    *,
    username: str = "ana",
    display_name: str = "Ana Souza",
    password: str = DEFAULT_PASSWORD,
    is_admin: bool = False,
) -> User:
    return service_create_user(
        db, username=username, display_name=display_name, password=password, is_admin=is_admin
    )


def create_session(
    db: Session,
    user: User,
    *,
    client: SessionClient = SessionClient.APP,
    device_name: str | None = "Pixel 8",
    expires_in: timedelta = timedelta(days=180),
) -> tuple[UserSession, str]:
    token = new_token()
    now = utcnow()
    user_session = UserSession(
        user_id=user.id,
        token_hash=hash_token(token),
        client=client,
        device_name=device_name,
        last_used_at=now,
        expires_at=now + expires_in,
    )
    db.add(user_session)
    db.commit()
    return user_session, token


def create_session_token(
    db: Session,
    user: User,
    *,
    client: SessionClient = SessionClient.APP,
    expires_in: timedelta = timedelta(days=180),
) -> str:
    return create_session(db, user, client=client, expires_in=expires_in)[1]
