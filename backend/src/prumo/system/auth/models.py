from datetime import datetime
from enum import StrEnum

from sqlalchemy import Enum, Index, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column

from prumo.core.clock import utcnow
from prumo.core.db import Base, IdMixin, TimestampMixin, UserOwnedMixin


class SessionClient(StrEnum):
    WEB = "web"
    APP = "app"


class UserSession(Base, IdMixin, TimestampMixin, UserOwnedMixin):
    """An opaque-token session. Only the SHA-256 of the token is stored."""

    __tablename__ = "user_sessions"

    token_hash: Mapped[bytes] = mapped_column(LargeBinary(32), unique=True)
    client: Mapped[SessionClient] = mapped_column(
        Enum(
            SessionClient,
            name="session_client",
            native_enum=False,
            create_constraint=True,
            length=8,
            values_callable=lambda enum: [member.value for member in enum],
        )
    )
    device_name: Mapped[str | None] = mapped_column(String(120))
    last_used_at: Mapped[datetime] = mapped_column(default=utcnow)
    expires_at: Mapped[datetime]
    revoked_at: Mapped[datetime | None]


class LoginAttempt(Base, IdMixin):
    """Login attempts, used to rate-limit by username and IP. Old rows are pruned on login."""

    __tablename__ = "login_attempts"
    __table_args__ = (Index("ix_login_attempts_lookup", "username", "ip", "attempted_at"),)

    username: Mapped[str] = mapped_column(String(64))
    ip: Mapped[str] = mapped_column(String(64))
    succeeded: Mapped[bool]
    attempted_at: Mapped[datetime] = mapped_column(default=utcnow)
