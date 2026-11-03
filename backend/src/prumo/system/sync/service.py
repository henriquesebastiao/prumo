"""Incremental sync (D41): what was deleted since the last sync."""

from datetime import datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from prumo.core.clock import utcnow
from prumo.core.errors import DomainError
from prumo.core.pagination import PageParams, paginate
from prumo.system.sync.models import SyncDeletion
from prumo.system.sync.schemas import DeletionPage, DeletionRead
from prumo.system.users.models import User

RETENTION = timedelta(days=180)


class SinceTooOldError(DomainError):
    status_code = 410
    default_code = "sync.since_too_old"
    default_message = "Deletions older than 180 days are gone: reload everything."


def list_deletions(session: Session, user: User, since: datetime, page: PageParams) -> DeletionPage:
    now = utcnow()
    limit = now - RETENTION
    if since < limit:
        raise SinceTooOldError(details={"oldest": limit.isoformat()})
    session.execute(
        delete(SyncDeletion).where(SyncDeletion.user_id == user.id, SyncDeletion.deleted_at < limit)
    )
    session.commit()
    stmt = select(SyncDeletion).where(
        SyncDeletion.user_id == user.id, SyncDeletion.deleted_at > since
    )
    result = paginate(
        session,
        stmt.order_by(SyncDeletion.deleted_at, SyncDeletion.id),
        page,
    )
    return DeletionPage(
        items=[
            DeletionRead(resource=row.resource, id=row.record_id, deleted_at=row.deleted_at)
            for row in result.items
        ],
        total=result.total,
        limit=page.limit,
        offset=page.offset,
        server_time=now,
    )
