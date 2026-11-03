from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Query
from pydantic import AfterValidator

from prumo.core.deps import SessionDep
from prumo.core.errors import error_responses
from prumo.core.pagination import PageDep, as_utc
from prumo.system.auth.deps import CurrentUser
from prumo.system.sync import service
from prumo.system.sync.schemas import DeletionPage

router = APIRouter(prefix="/sync", tags=["sync"], responses=error_responses(401, 403, 410, 422))

Since = Annotated[
    datetime,
    AfterValidator(as_utc),
    Query(description="The `server_time` of the last sync (without time zone: UTC)."),
]


@router.get("/deletions")
def list_deletions(
    session: SessionDep, user: CurrentUser, page: PageDep, since: Since
) -> DeletionPage:
    """Records deleted after `since`, oldest first, with the cursor of the next sync (D41).
    Kept for 180 days; an older `since` answers 410 `sync.since_too_old`."""
    return service.list_deletions(session, user, since, page)
