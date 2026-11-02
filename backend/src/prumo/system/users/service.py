import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from prumo.core.errors import ConflictError, DomainError
from prumo.core.modules import registry
from prumo.core.security import hash_password
from prumo.system.preferences.service import create_default_preferences
from prumo.system.users.models import User
from prumo.system.users.schemas import UserUpdate

USERNAME = re.compile(r"^[a-z0-9][a-z0-9._-]{1,31}$")
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128


def normalize_username(username: str) -> str:
    return username.strip().lower()


def validate_password(password: str) -> None:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise DomainError(
            "Password is too short.",
            code="users.password_too_short",
            details={"min_length": MIN_PASSWORD_LENGTH},
        )
    if len(password) > MAX_PASSWORD_LENGTH:
        raise DomainError(
            "Password is too long.",
            code="users.password_too_long",
            details={"max_length": MAX_PASSWORD_LENGTH},
        )


def get_by_username(session: Session, username: str) -> User | None:
    return session.scalar(select(User).where(User.username == normalize_username(username)))


def create_user(
    session: Session,
    *,
    username: str,
    display_name: str,
    password: str,
    is_admin: bool = False,
) -> User:
    """Creates a user with default preferences and runs every module's `on_user_created` (S1)."""
    username = normalize_username(username)
    if not USERNAME.match(username):
        raise DomainError(
            "Username must have 2 to 32 characters: letters, digits, '.', '_' or '-'.",
            code="users.invalid_username",
        )
    display_name = display_name.strip()
    if not 1 <= len(display_name) <= 80:
        raise DomainError("Display name must have 1 to 80 characters.", code="users.invalid_name")
    validate_password(password)
    if get_by_username(session, username) is not None:
        raise ConflictError("Username already in use.", code="users.username_taken")

    user = User(
        username=username,
        display_name=display_name,
        password_hash=hash_password(password),
        is_admin=is_admin,
    )
    session.add(user)
    session.flush()
    create_default_preferences(session, user)
    for module in registry.modules:
        if module.on_user_created is not None:
            module.on_user_created(session, user)
    session.commit()
    return user


def set_password(session: Session, user: User, password: str) -> None:
    validate_password(password)
    user.password_hash = hash_password(password)
    session.commit()


def update_profile(session: Session, user: User, data: UserUpdate) -> User:
    if data.display_name is not None:
        user.display_name = data.display_name
    session.commit()
    return user
