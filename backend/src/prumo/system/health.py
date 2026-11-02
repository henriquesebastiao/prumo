from typing import Literal

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from prumo import __version__
from prumo.core.deps import SessionDep

router = APIRouter(tags=["system"])


class Health(BaseModel):
    status: Literal["ok", "degraded"]
    database: Literal["ok", "unavailable"]
    version: str


@router.get(
    "/health",
    response_model=Health,
    responses={503: {"model": Health, "description": "Database unavailable"}},
)
def health(session: SessionDep) -> Health | JSONResponse:
    """Liveness and database check. No authentication, no version prefix."""
    try:
        session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        body = Health(status="degraded", database="unavailable", version=__version__)
        return JSONResponse(body.model_dump(), status_code=503)
    return Health(status="ok", database="ok", version=__version__)
