from datetime import date, datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field, StringConstraints

from prumo.core.modules import ModuleSummary
from prumo.core.schemas import reject_null
from prumo.modules.reading.models import BookStatus

Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Author = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
Pages = Annotated[int, Field(ge=1, le=100_000)]
Page = Annotated[int, Field(ge=0, le=100_000)]
NoteText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=10_000)]


class BookRef(BaseModel):
    id: UUID
    title: str
    author: str


# ---------------------------------------------------------------- books


class BookCreate(BaseModel):
    title: Title
    author: Author
    total_pages: Pages
    status: BookStatus = BookStatus.WANT_TO_READ
    owned: bool = Field(default=False, description="'Tenho': independent from the status (R1).")
    current_page: Page = Field(default=0, description="For a book already started (R3, R4).")
    started_on: date | None = Field(default=None, description="Defaults to today when reading.")
    finished_on: date | None = Field(default=None, description="Defaults to today when read.")


class BookUpdate(BaseModel):
    """Status changes fill empty dates like the progress does (R3, R4)."""

    title: Title | None = None
    author: Author | None = None
    total_pages: Pages | None = None
    status: BookStatus | None = None
    owned: bool | None = None
    started_on: date | None = None
    finished_on: date | None = None

    _not_null = reject_null("title", "author", "total_pages", "status", "owned")


class WeekPages(BaseModel):
    week_start: date = Field(description="Monday of the week.")
    pages: int


class BookRead(BaseModel):
    id: UUID
    title: str
    author: str
    total_pages: int
    current_page: int
    status: BookStatus
    owned: bool
    started_on: date | None
    finished_on: date | None
    has_cover: bool
    cover_updated_at: datetime | None = Field(description="Changes when the cover changes.")
    created_at: datetime
    progress_percent: int = Field(description="R5.")
    remaining_pages: int
    pace_pages_per_day: float | None = Field(description="R7: last 14 days.")
    forecast_finish_on: date | None = Field(description="R8.")
    last_progress_at: datetime | None
    notes_count: int


class BookDetail(BookRead):
    weekly_pages: list[WeekPages] = Field(description="R9.")


class ProgressCreate(BaseModel):
    page: Page


class ProgressRead(BaseModel):
    id: UUID
    page: int
    previous_page: int
    pages: int = Field(description="Pages advanced (negative for a correction).")
    recorded_at: datetime


class ProgressList(BaseModel):
    items: list[ProgressRead]


# ---------------------------------------------------------------- notes


class NoteCreate(BaseModel):
    content: NoteText = Field(description="Simple markdown.")
    page: Page | None = None
    noted_on: date | None = Field(default=None, description="Defaults to today.")


class NoteUpdate(BaseModel):
    content: NoteText | None = None
    page: Page | None = None
    noted_on: date | None = None

    _not_null = reject_null("content", "noted_on")


class NoteRead(BaseModel):
    id: UUID
    book: BookRef
    content: str
    page: int | None
    noted_on: date
    created_at: datetime
    updated_at: datetime


class NoteList(BaseModel):
    items: list[NoteRead]


# ---------------------------------------------------------------- overview and summary


class ReadingOverview(BaseModel):
    books_count: int
    want_to_read_count: int
    reading_count: int
    read_count: int
    notes_count: int


class ShelfBook(BaseModel):
    book: BookRef
    status: BookStatus
    total_pages: int
    finished_on: date | None


class CurrentBook(BaseModel):
    book: BookRef
    current_page: int
    total_pages: int
    progress_percent: int
    has_cover: bool
    cover_updated_at: datetime | None


class ReadingSummary(ModuleSummary):
    module: Literal["reading"] = "reading"
    books_count: int
    current: CurrentBook | None = Field(description="The book read most recently.")
    shelf: list[ShelfBook] = Field(description="Last book read and next one to read.")
