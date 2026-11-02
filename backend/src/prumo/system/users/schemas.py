from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator
from pydantic_core import PydanticCustomError

DisplayName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]
Password = Annotated[str, Field(min_length=8, max_length=128)]


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    display_name: str
    is_admin: bool
    created_at: datetime
    updated_at: datetime


class UserUpdate(BaseModel):
    display_name: DisplayName | None = None

    @field_validator("display_name", mode="before")
    @classmethod
    def _not_null(cls, value: object) -> object:
        if value is None:
            raise PydanticCustomError("not_nullable", "Field cannot be null.")
        return value


class PasswordChange(BaseModel):
    current_password: str
    new_password: Password
