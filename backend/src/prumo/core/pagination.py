"""Standard list format: `{"items": [...], "total": n, "limit": n, "offset": n}`.

Endpoints declare the sortable fields with `sort_param(...)` and paginate with `paginate(...)`.
"""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import Depends, Query
from fastapi.exceptions import RequestValidationError
from pydantic import AfterValidator, BaseModel
from sqlalchemy import ColumnElement, Select, func, select
from sqlalchemy.orm import QueryableAttribute, Session

type SortColumn = ColumnElement[Any] | QueryableAttribute[Any]

DEFAULT_LIMIT = 50
MAX_LIMIT = 200


@dataclass(frozen=True)
class PageParams:
    limit: int = DEFAULT_LIMIT
    offset: int = 0


def page_params(
    limit: Annotated[int, Query(ge=1, le=MAX_LIMIT)] = DEFAULT_LIMIT,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PageParams:
    return PageParams(limit=limit, offset=offset)


PageDep = Annotated[PageParams, Depends(page_params)]


def as_utc[T: (datetime, datetime | None)](value: T) -> T:
    """A moment without time zone is read as UTC."""
    if isinstance(value, datetime) and value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


UpdatedSince = Annotated[
    datetime | None,
    AfterValidator(as_utc),
    Query(
        description=(
            "Only records created or changed after this moment, archived ones included, oldest "
            "change first; `sort` is ignored (incremental sync, D41)."
        )
    ),
]


class Page[T](BaseModel):
    items: list[T]
    total: int
    limit: int
    offset: int


@dataclass(frozen=True)
class Sort:
    field: str
    descending: bool

    @property
    def token(self) -> str:
        return f"-{self.field}" if self.descending else self.field


def sort_param(*fields: str, default: str) -> Callable[..., Sort]:
    """Builds a `sort` query dependency accepting `field` or `-field` for the given fields."""
    allowed = set(fields)
    tokens = sorted({*fields, *(f"-{field}" for field in fields)})
    description = "One of: " + ", ".join(tokens) + ". A leading `-` sorts descending."

    def dependency(
        sort: Annotated[str, Query(description=description)] = default,
    ) -> Sort:
        descending = sort.startswith("-")
        field = sort.removeprefix("-")
        if field not in allowed:
            raise RequestValidationError(
                [
                    {
                        "loc": ("query", "sort"),
                        "type": "enum",
                        "msg": f"Input should be one of: {', '.join(tokens)}",
                        "input": sort,
                    }
                ]
            )
        return Sort(field=field, descending=descending)

    return dependency


def paginate[M](
    session: Session,
    stmt: Select[M],
    page: PageParams,
    *,
    sort: Sort | None = None,
    sort_columns: Mapping[str, SortColumn] | None = None,
    tiebreaker: Sequence[SortColumn] = (),
    updated_since: datetime | None = None,
) -> Page[M]:
    """`updated_since` (D41) keeps the records of the selected entity changed after that moment,
    ordered by `updated_at`, instead of the requested sort."""
    if updated_since is not None:
        entity = stmt.column_descriptions[0]["entity"]
        stmt = stmt.where(entity.updated_at > updated_since)
        total = session.scalar(select(func.count()).select_from(stmt.order_by(None).subquery()))
        ordered = stmt.order_by(None).order_by(entity.updated_at, entity.id)
        items = list(session.scalars(ordered.limit(page.limit).offset(page.offset)))
        return Page[M](items=items, total=total or 0, limit=page.limit, offset=page.offset)
    total = session.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    if sort is not None:
        if sort_columns is None or sort.field not in sort_columns:
            msg = f"No column mapped for sort field {sort.field!r}"
            raise ValueError(msg)
        column = sort_columns[sort.field]
        stmt = stmt.order_by(column.desc() if sort.descending else column.asc())
    stmt = stmt.order_by(*tiebreaker)
    items = list(session.scalars(stmt.limit(page.limit).offset(page.offset)))
    return Page[M](items=items, total=total, limit=page.limit, offset=page.offset)
