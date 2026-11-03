"""Reading tables and covers in the user data export (D38)."""

from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from prumo.core.export import ModuleExport, table_rows
from prumo.modules.reading import covers
from prumo.modules.reading.models import Book, BookNote, ReadingProgress
from prumo.system.users.models import User


def build_export(session: Session, user: User) -> ModuleExport:
    files: dict[str, Path] = {}
    for book_id in session.scalars(
        select(Book.id).where(Book.user_id == user.id, Book.cover_updated_at.is_not(None))
    ):
        path = covers.path_for(book_id)
        if path.is_file():
            files[f"covers/{book_id}.webp"] = path
    return ModuleExport(
        tables={
            "books": table_rows(session, Book, user.id),
            "progress": table_rows(session, ReadingProgress, user.id),
            "notes": table_rows(session, BookNote, user.id),
        },
        files=files,
    )
