"""Domain errors and the single error format of the API.

Services raise `DomainError` (or a subclass), never `HTTPException`. The handlers installed by
`install_error_handlers` turn every error, including validation and framework errors, into:

    {"error": {"code": "...", "message": "...", "details": {...}, "fields": [...]}}
"""

import logging
from collections.abc import Mapping
from http import HTTPStatus
from typing import Any, ClassVar

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

_LOCATIONS = {"body", "query", "path", "header", "cookie"}


class ErrorField(BaseModel):
    path: str
    code: str
    message: str


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None
    fields: list[ErrorField] | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody


class DomainError(Exception):
    """A business rule was violated. Subclasses set the HTTP status and a default code."""

    status_code: ClassVar[int] = 422
    default_code: ClassVar[str] = "domain_error"
    default_message: ClassVar[str] = "Business rule violated."

    def __init__(
        self,
        message: str | None = None,
        *,
        code: str | None = None,
        details: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> None:
        self.code = code or self.default_code
        self.message = message or self.default_message
        self.details = dict(details) if details else None
        self.headers = dict(headers) if headers else None
        super().__init__(self.message)


class NotFoundError(DomainError):
    """Missing resource, or a resource that belongs to another user (never 403)."""

    status_code = 404
    default_code = "not_found"
    default_message = "Resource not found."


class ConflictError(DomainError):
    status_code = 409
    default_code = "conflict"
    default_message = "Resource already exists."


class AuthenticationError(DomainError):
    status_code = 401
    default_code = "auth.required"
    default_message = "Authentication required."


class ForbiddenError(DomainError):
    status_code = 403
    default_code = "forbidden"
    default_message = "Forbidden."


class RateLimitedError(DomainError):
    status_code = 429
    default_code = "rate_limited"
    default_message = "Too many attempts."


def error_responses(*statuses: int) -> dict[int | str, dict[str, Any]]:
    """OpenAPI `responses` entries documenting the standard error body for the given statuses."""
    return {
        status: {"model": ErrorResponse, "description": HTTPStatus(status).phrase}
        for status in statuses
    }


def _body(
    code: str,
    message: str,
    *,
    details: Mapping[str, Any] | None = None,
    fields: list[ErrorField] | None = None,
) -> dict[str, Any]:
    error = ErrorBody(
        code=code,
        message=message,
        details=dict(details) if details else None,
        fields=fields,
    )
    return ErrorResponse(error=error).model_dump(mode="json", exclude_none=True)


def _field_path(loc: tuple[int | str, ...]) -> str:
    parts = list(loc)
    if len(parts) > 1 and parts[0] in _LOCATIONS:
        parts = parts[1:]
    return ".".join(str(part) for part in parts)


async def _domain_error_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, DomainError)
    return JSONResponse(
        _body(exc.code, exc.message, details=exc.details),
        status_code=exc.status_code,
        headers=exc.headers,
    )


async def _validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    fields = [
        ErrorField(path=_field_path(tuple(err["loc"])), code=err["type"], message=err["msg"])
        for err in exc.errors()
    ]
    return JSONResponse(
        _body("validation_error", "Invalid request.", fields=fields), status_code=422
    )


_HTTP_CODES = {
    401: "auth.required",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    429: "rate_limited",
}


async def _http_error_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)
    code = _HTTP_CODES.get(exc.status_code, "http_error")
    message = exc.detail if isinstance(exc.detail, str) else HTTPStatus(exc.status_code).phrase
    return JSONResponse(
        _body(code, message), status_code=exc.status_code, headers=getattr(exc, "headers", None)
    )


async def _unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path, exc_info=exc)
    return JSONResponse(_body("internal_error", "Internal server error."), status_code=500)


def _replace_validation_schema(node: Any) -> None:
    if isinstance(node, dict):
        if node.get("$ref") == "#/components/schemas/HTTPValidationError":
            node["$ref"] = "#/components/schemas/ErrorResponse"
        for value in node.values():
            _replace_validation_schema(value)
    elif isinstance(node, list):
        for value in node:
            _replace_validation_schema(value)


def document_standard_errors(app: FastAPI) -> None:
    """Makes the OpenAPI schema describe FastAPI's automatic 422 responses with `ErrorResponse`
    (what the handlers actually return) instead of FastAPI's default `HTTPValidationError`."""
    original = app.openapi

    def openapi() -> dict[str, Any]:
        if app.openapi_schema is not None:
            return app.openapi_schema
        schema = original()
        _replace_validation_schema(schema.get("paths", {}))
        components = schema.setdefault("components", {}).setdefault("schemas", {})
        components.pop("HTTPValidationError", None)
        components.pop("ValidationError", None)
        app.openapi_schema = schema
        return schema

    app.openapi = openapi  # type: ignore[method-assign]


def install_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, _domain_error_handler)
    app.add_exception_handler(RequestValidationError, _validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, _http_error_handler)
    app.add_exception_handler(Exception, _unexpected_error_handler)
