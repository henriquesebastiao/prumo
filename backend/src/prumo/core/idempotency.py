"""Idempotent creation (D40): a POST may carry the record's `id` (UUID v7) chosen by the client.

Repeating the request with the same `id` returns the record already created (200) instead of a
duplicate. The id of another user's record is a conflict (409 `id_conflict`).
"""

from collections.abc import Callable
from typing import Annotated, Any
from uuid import UUID

from fastapi import Response, status
from pydantic import AfterValidator, Field
from pydantic_core import PydanticCustomError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from prumo.core.errors import ConflictError, error_responses


def _uuid7(value: UUID) -> UUID:
    if value.version != 7:
        raise PydanticCustomError("uuid_version", "Use a UUID version 7.")
    return value


ClientId = Annotated[
    UUID,
    AfterValidator(_uuid7),
    Field(description="Id chosen by the client (UUID v7). Repeating it returns the record (D40)."),
]


def created_responses(model: type[Any]) -> dict[int | str, dict[str, Any]]:
    """OpenAPI responses of an idempotent POST: 200 when the id was already used, 409 conflict."""
    return {
        200: {"model": model, "description": "Already created with this `id` (nothing changed)."},
        **error_responses(409),
    }


def find_existing[M](session: Session, model: type[M], user_id: UUID, record_id: UUID) -> M | None:
    """The user's record with this id, or None; the id of another user's record is a conflict."""
    found = session.get(model, record_id)
    if found is None:
        return None
    if getattr(found, "user_id", None) != user_id:
        raise ConflictError("This id is already in use.", code="id_conflict")
    return found


def create_once[M](
    session: Session,
    model: type[M],
    user_id: UUID,
    record_id: UUID | None,
    response: Response,
    create: Callable[[], M],
) -> M:
    """Runs `create`, unless the record with `record_id` already exists (then answers 200)."""
    if record_id is not None and (found := find_existing(session, model, user_id, record_id)):
        response.status_code = status.HTTP_200_OK
        return found
    try:
        return create()
    except IntegrityError:
        # Two identical requests at the same time: the second one finds the first record.
        session.rollback()
        if (
            record_id is None
            or (found := find_existing(session, model, user_id, record_id)) is None
        ):
            raise
        response.status_code = status.HTTP_200_OK
        return found
