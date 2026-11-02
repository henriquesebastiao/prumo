from enum import StrEnum
from uuid import UUID

from sqlalchemy import ARRAY, Enum, ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column

from prumo.core.db import Base, TimestampMixin


class Theme(StrEnum):
    SYSTEM = "system"
    LIGHT = "light"
    DARK = "dark"


class UserPreferences(Base, TimestampMixin):
    """One row per user.

    Module state is stored as an order plus a set of disabled ids, so that a module installed
    later shows up enabled (at the end) for existing users. The API exposes it as the ordered
    `enabled_modules` list (see preferences.service).
    """

    __tablename__ = "user_preferences"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    theme: Mapped[Theme] = mapped_column(
        Enum(
            Theme,
            name="theme",
            native_enum=False,
            create_constraint=True,
            length=8,
            values_callable=lambda enum: [member.value for member in enum],
        ),
        default=Theme.SYSTEM,
    )
    locale: Mapped[str] = mapped_column(String(16))
    timezone: Mapped[str] = mapped_column(String(64))
    currency: Mapped[str] = mapped_column(String(3))
    module_order: Mapped[list[str]] = mapped_column(
        ARRAY(String(32)), default=list, server_default=text("'{}'")
    )
    disabled_modules: Mapped[list[str]] = mapped_column(
        ARRAY(String(32)), default=list, server_default=text("'{}'")
    )
