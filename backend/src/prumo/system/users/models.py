from sqlalchemy import String, false
from sqlalchemy.orm import Mapped, mapped_column

from prumo.core.db import Base, IdMixin, TimestampMixin


class User(Base, IdMixin, TimestampMixin):
    __tablename__ = "users"

    # Stored normalized (lowercase); see users.service.normalize_username.
    username: Mapped[str] = mapped_column(String(32), unique=True)
    display_name: Mapped[str] = mapped_column(String(80))
    password_hash: Mapped[str] = mapped_column(String(255))
    is_admin: Mapped[bool] = mapped_column(default=False, server_default=false())
