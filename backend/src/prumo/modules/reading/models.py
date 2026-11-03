from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from prumo.core.db import Base, IdMixin, TimestampMixin, UserOwnedMixin, string_enum


class BookStatus(StrEnum):
    WANT_TO_READ = "want_to_read"
    READING = "reading"
    READ = "read"


class Book(Base, IdMixin, TimestampMixin, UserOwnedMixin):
    __tablename__ = "reading_books"
    __table_args__ = (
        Index("ix_reading_books_user_status", "user_id", "status"),
        CheckConstraint("total_pages > 0", name="total_pages_positive"),
        CheckConstraint("current_page BETWEEN 0 AND total_pages", name="current_page_range"),
        CheckConstraint(
            "finished_on IS NULL OR started_on IS NULL OR finished_on >= started_on",
            name="dates_order",
        ),
    )

    title: Mapped[str] = mapped_column(String(200))
    author: Mapped[str] = mapped_column(String(120))
    total_pages: Mapped[int]
    current_page: Mapped[int] = mapped_column(default=0)
    status: Mapped[BookStatus] = mapped_column(string_enum(BookStatus, "book_status"))
    owned: Mapped[bool] = mapped_column(default=False)
    started_on: Mapped[date | None]
    finished_on: Mapped[date | None]
    # Set when a cover is stored (R6); also the version clients use to refresh the image.
    cover_updated_at: Mapped[datetime | None]


class ReadingProgress(Base, IdMixin, TimestampMixin, UserOwnedMixin):
    __tablename__ = "reading_progress"
    __table_args__ = (
        Index("ix_reading_progress_book_time", "book_id", "recorded_at"),
        CheckConstraint("page >= 0", name="page_positive"),
        CheckConstraint("previous_page >= 0", name="previous_page_positive"),
    )

    book_id: Mapped[UUID] = mapped_column(ForeignKey("reading_books.id", ondelete="CASCADE"))
    page: Mapped[int]
    previous_page: Mapped[int]
    recorded_at: Mapped[datetime]

    @property
    def pages(self) -> int:
        """Pages advanced by this record (negative for a correction)."""
        return self.page - self.previous_page


class BookNote(Base, IdMixin, TimestampMixin, UserOwnedMixin):
    __tablename__ = "reading_notes"
    __table_args__ = (
        Index("ix_reading_notes_book_day", "book_id", "noted_on"),
        CheckConstraint("page IS NULL OR page >= 0", name="page_positive"),
    )

    book_id: Mapped[UUID] = mapped_column(ForeignKey("reading_books.id", ondelete="CASCADE"))
    content: Mapped[str] = mapped_column(Text)
    page: Mapped[int | None]
    noted_on: Mapped[date]
