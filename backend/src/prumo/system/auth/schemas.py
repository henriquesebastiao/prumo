from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from prumo.system.auth.models import SessionClient
from prumo.system.users.schemas import UserRead


class LoginRequest(BaseModel):
    username: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=64)]
    password: Annotated[str, Field(min_length=1, max_length=256)]
    client: SessionClient = Field(
        description="`web`: the session goes in the `prumo_session` cookie. "
        "`app`: the token is returned in the body, to be sent as `Authorization: Bearer`."
    )
    device_name: Annotated[
        str | None, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)
    ] = Field(default=None, description="Shown in the session list. Web derives it if omitted.")
    remember: bool = Field(
        default=True,
        description="Web only. `false` creates a short session whose cookie ends with the browser.",
    )


class LoginResponse(BaseModel):
    user: UserRead
    expires_at: datetime
    token: str | None = Field(
        default=None, description="Session token. Only returned when `client` is `app`."
    )


class SessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    client: SessionClient
    device_name: str | None
    current: bool = Field(description="Whether this is the session making the request.")
    last_used_at: datetime
    expires_at: datetime
    created_at: datetime
    updated_at: datetime


class SessionList(BaseModel):
    items: list[SessionRead]
