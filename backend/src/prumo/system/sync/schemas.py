from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from prumo.core.pagination import Page


class DeletionRead(BaseModel):
    resource: str = Field(
        description="`<module>.<table>`, as in the data export: `garage.vehicles`."
    )
    id: UUID
    deleted_at: datetime


class DeletionPage(Page[DeletionRead]):
    server_time: datetime = Field(description="Cursor of the next sync (use it as `since`).")
