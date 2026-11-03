from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, Response, UploadFile, status
from fastapi.responses import FileResponse

from prumo.core.deps import SessionDep
from prumo.core.errors import error_responses
from prumo.core.idempotency import create_once, created_responses, find_existing
from prumo.core.pagination import Page, PageDep, Sort, sort_param
from prumo.modules.reading import covers, service
from prumo.modules.reading.models import Book, BookNote, BookStatus, ReadingProgress
from prumo.modules.reading.schemas import (
    BookCreate,
    BookDetail,
    BookRead,
    BookUpdate,
    NoteCreate,
    NoteList,
    NoteRead,
    NoteUpdate,
    ProgressCreate,
    ProgressList,
    ReadingOverview,
)
from prumo.system.auth.deps import CurrentUser

router = APIRouter(responses=error_responses(401, 403, 404, 422))

BookSort = Annotated[
    Sort,
    Depends(sort_param("created_at", "title", "author", "finished_on", default="-created_at")),
]


def _book(book_id: UUID, session: SessionDep, user: CurrentUser) -> Book:
    return service.get_book(session, user, book_id)


BookDep = Annotated[Book, Depends(_book)]


def _note(note_id: UUID, book: BookDep, session: SessionDep) -> BookNote:
    return service.get_note(session, book, note_id)


NoteDep = Annotated[BookNote, Depends(_note)]


@router.get("/overview")
def read_overview(session: SessionDep, user: CurrentUser) -> ReadingOverview:
    """Books by status and the number of notes."""
    return service.overview(session, user)


# ---------------------------------------------------------------- books


@router.get("/books")
def list_books(
    session: SessionDep,
    user: CurrentUser,
    page: PageDep,
    sort: BookSort,
    status: BookStatus | None = None,
    owned: bool | None = None,
    q: Annotated[str | None, Query(max_length=120, description="Title or author.")] = None,
) -> Page[BookRead]:
    return service.list_books(session, user, page, status=status, owned=owned, q=q, sort=sort)


@router.post("/books", status_code=status.HTTP_201_CREATED, responses=created_responses(BookRead))
def create_book(
    data: BookCreate, session: SessionDep, user: CurrentUser, response: Response
) -> BookRead:
    book = create_once(
        session,
        Book,
        user.id,
        data.id,
        response,
        lambda: service.create_book(session, user, data),
    )
    return service.book_read(session, user, book)


@router.get("/books/{book_id}")
def read_book(book: BookDep, session: SessionDep, user: CurrentUser) -> BookDetail:
    return service.book_detail(session, user, book)


@router.patch("/books/{book_id}")
def update_book(
    data: BookUpdate, book: BookDep, session: SessionDep, user: CurrentUser
) -> BookRead:
    return service.book_read(session, user, service.update_book(session, user, book, data))


@router.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(book: BookDep, session: SessionDep) -> None:
    """Removes the book with its progress, notes and cover."""
    service.delete_book(session, book)


@router.get("/books/{book_id}/progress")
def list_progress(book: BookDep, session: SessionDep) -> ProgressList:
    return ProgressList(items=service.list_progress(session, book))


@router.post(
    "/books/{book_id}/progress",
    status_code=status.HTTP_201_CREATED,
    responses=created_responses(BookRead),
)
def add_progress(
    data: ProgressCreate, book: BookDep, session: SessionDep, user: CurrentUser, response: Response
) -> BookRead:
    """R2-R4: records the current page; the status and dates follow. `id` is the progress
    record's; repeating it returns the book unchanged."""
    if (
        data.id is not None
        and find_existing(session, ReadingProgress, user.id, data.id) is not None
    ):
        response.status_code = status.HTTP_200_OK
        return service.book_read(session, user, book)
    return service.book_read(
        session, user, service.add_progress(session, user, book, data.page, record_id=data.id)
    )


# ---------------------------------------------------------------- cover (R6)


@router.get(
    "/books/{book_id}/cover",
    response_class=FileResponse,
    responses={200: {"content": {"image/webp": {}}, "description": "The cover (WebP)."}},
)
def read_cover(book: BookDep) -> FileResponse:
    return FileResponse(
        service.cover_path(book),
        media_type="image/webp",
        headers={"Cache-Control": "private, max-age=86400"},
    )


@router.put("/books/{book_id}/cover", responses=error_responses(413))
def set_cover(
    file: Annotated[UploadFile, File(description="JPEG, PNG or WebP up to 5 MB.")],
    book: BookDep,
    session: SessionDep,
    user: CurrentUser,
) -> BookRead:
    data = file.file.read(covers.MAX_BYTES + 1)
    return service.book_read(session, user, service.set_cover(session, book, data))


@router.delete("/books/{book_id}/cover", status_code=status.HTTP_204_NO_CONTENT)
def delete_cover(book: BookDep, session: SessionDep) -> None:
    service.remove_cover(session, book)


# ---------------------------------------------------------------- notes


@router.get("/notes")
def list_notes(
    session: SessionDep,
    user: CurrentUser,
    page: PageDep,
    q: Annotated[str | None, Query(max_length=120, description="Text of the note.")] = None,
) -> Page[NoteRead]:
    """R10: every note, newest first, with its book."""
    return service.list_notes(session, user, page, q=q)


@router.get("/books/{book_id}/notes")
def list_book_notes(book: BookDep, session: SessionDep) -> NoteList:
    return NoteList(items=service.list_book_notes(session, book))


@router.post(
    "/books/{book_id}/notes",
    status_code=status.HTTP_201_CREATED,
    responses=created_responses(NoteRead),
)
def create_note(
    data: NoteCreate, book: BookDep, session: SessionDep, user: CurrentUser, response: Response
) -> NoteRead:
    note = create_once(
        session,
        BookNote,
        user.id,
        data.id,
        response,
        lambda: service.create_note(session, user, book, data),
    )
    return service.note_read(note, book)


@router.patch("/books/{book_id}/notes/{note_id}")
def update_note(data: NoteUpdate, note: NoteDep, book: BookDep, session: SessionDep) -> NoteRead:
    return service.note_read(service.update_note(session, book, note, data), book)


@router.delete("/books/{book_id}/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(note: NoteDep, session: SessionDep) -> None:
    service.delete_note(session, note)
