from datetime import datetime
from uuid import UUID

from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column

from prumo.core.db import Base, IdMixin


class SyncDeletion(Base, IdMixin):
    """A deleted record (D41), written by the `prumo_record_deletion` trigger of each module
    table. No foreign key to users: rows of a deleted user are simply not written."""

    __tablename__ = "sync_deletions"
    __table_args__ = (Index("ix_sync_deletions_user_time", "user_id", "deleted_at"),)

    user_id: Mapped[UUID]
    resource: Mapped[str] = mapped_column(String(64))
    record_id: Mapped[UUID]
    deleted_at: Mapped[datetime]
