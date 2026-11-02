"""Helpers shared by request and response schemas."""

from typing import Any

from pydantic import field_validator
from pydantic_core import PydanticCustomError


def reject_null(*fields: str) -> Any:
    """Field validator for PATCH schemas: the fields may be absent, but not `null`.

    Usage, in the class body: `_not_null = reject_null("name", "year")`.
    """

    def check(cls: type, value: object) -> object:
        if value is None:
            raise PydanticCustomError("not_nullable", "Field cannot be null.")
        return value

    return field_validator(*fields, mode="before")(check)
