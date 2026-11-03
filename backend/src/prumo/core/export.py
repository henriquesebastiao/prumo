"""Building blocks of the user data export (D38): a module turns its tables into rows."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

type Value = str | int | float | bool | None

HIDDEN = frozenset({"user_id"})


@dataclass(frozen=True)
class ExportTable:
    columns: Sequence[str]
    rows: Sequence[Mapping[str, Value]]


@dataclass(frozen=True)
class ModuleExport:
    """What a module exports: tables by name and files by their path inside the archive."""

    tables: Mapping[str, ExportTable]
    files: Mapping[str, Path] = field(default_factory=dict)


def plain(value: object) -> Value:
    """A value that JSON and CSV can hold."""
    if value is None or isinstance(value, bool | int | float | str):
        return value
    if isinstance(value, Enum):
        return plain(value.value)
    if isinstance(value, UUID | Decimal):
        return str(value)
    if isinstance(value, datetime | date | time):
        return value.isoformat()
    return str(value)


def table_rows(session: Session, model: type[Any], user_id: UUID) -> ExportTable:
    """Every row of a user-owned model, oldest first, without `user_id`."""
    columns = [c.key for c in inspect(model).column_attrs if c.key not in HIDDEN]
    stmt = select(model).where(model.user_id == user_id)
    order = [getattr(model, name) for name in ("created_at", "id") if name in columns]
    items = session.scalars(stmt.order_by(*order))
    return ExportTable(
        columns=columns,
        rows=[{name: plain(getattr(item, name)) for name in columns} for item in items],
    )
