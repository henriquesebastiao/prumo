from datetime import datetime
from typing import Annotated, Literal
from zoneinfo import available_timezones

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_core import PydanticCustomError

from prumo.core.modules import registry
from prumo.system.preferences.models import Theme

Locale = Literal["pt-BR"]
Currency = Annotated[str, Field(pattern=r"^[A-Z]{3}$", examples=["BRL"])]


class PreferencesRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    theme: Theme
    locale: Locale
    timezone: str = Field(examples=["America/Sao_Paulo"])
    currency: Currency
    enabled_modules: list[str] = Field(
        description="Enabled module ids, in navigation and dashboard order."
    )
    created_at: datetime
    updated_at: datetime


class PreferencesUpdate(BaseModel):
    """Partial update: absent fields are left unchanged. None of these fields accepts null."""

    theme: Theme | None = None
    locale: Locale | None = None
    timezone: str | None = None
    currency: Currency | None = None
    enabled_modules: list[str] | None = Field(
        default=None,
        description="Ordered list of enabled module ids. Installed modules left out are disabled.",
    )

    @field_validator("theme", "locale", "timezone", "currency", "enabled_modules", mode="before")
    @classmethod
    def _not_null(cls, value: object) -> object:
        if value is None:
            raise PydanticCustomError("not_nullable", "Field cannot be null.")
        return value

    @field_validator("timezone")
    @classmethod
    def _valid_timezone(cls, value: str | None) -> str | None:
        if value is not None and value not in available_timezones():
            raise PydanticCustomError("invalid_timezone", "Unknown IANA time zone.")
        return value

    @field_validator("enabled_modules")
    @classmethod
    def _valid_modules(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return value
        if len(set(value)) != len(value):
            raise PydanticCustomError("duplicate_items", "Module ids must be unique.")
        unknown = [module_id for module_id in value if module_id not in registry.ids]
        if unknown:
            raise PydanticCustomError(
                "unknown_module",
                "Unknown module: {modules}.",
                {"modules": ", ".join(unknown)},
            )
        return value
