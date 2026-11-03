"""Business rules of the reading module (docs/dominio.md, R1-R11)."""

from collections.abc import Iterable, Sequence
from datetime import date, datetime
from uuid import UUID, uuid7
from zoneinfo import ZoneInfo

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from prumo.core.clock import utcnow
from prumo.core.errors import DomainError, NotFoundError
from prumo.core.modules import ActivityItem
from prumo.core.pagination import Page, PageParams, Sort, SortColumn, paginate
from prumo.modules.reading import covers, rules
from prumo.modules.reading.models import Book, BookNote, BookStatus, ReadingProgress
from prumo.modules.reading.schemas import (
    BookCreate,
    BookDetail,
    BookRead,
    BookRef,
    BookUpdate,
    CurrentBook,
    NoteCreate,
    NoteRead,
    NoteUpdate,
    ProgressRead,
    ReadingOverview,
    ReadingSummary,
    ShelfBook,
    WeekPages,
)
from prumo.system.preferences.service import timezone_for
from prumo.system.users.models import User

ACTIVITY_LIMIT = 10
EXCERPT = 90


def _today(tz: ZoneInfo) -> date:
    return utcnow().astimezone(tz).date()


def _ref(book: Book) -> BookRef:
    return BookRef(id=book.id, title=book.title, author=book.author)


def _escape_like(text: str) -> str:
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


# ---------------------------------------------------------------- books


def get_book(session: Session, user: User, book_id: UUID) -> Book:
    book = session.scalar(select(Book).where(Book.id == book_id, Book.user_id == user.id))
    if book is None:
        raise NotFoundError()
    return book


def _check_dates(started_on: date | None, finished_on: date | None) -> None:
    if started_on and finished_on and finished_on < started_on:
        raise DomainError("The book cannot end before it starts.", code="reading.invalid_dates")


def _check_page(book: Book, page: int) -> None:
    if page > book.total_pages:
        raise DomainError(
            "Page is beyond the last page.",
            code="reading.page_out_of_range",
            details={"total_pages": book.total_pages},
        )


def _record(
    session: Session, book: Book, page: int, previous: int, record_id: UUID | None = None
) -> None:
    session.add(
        ReadingProgress(
            id=record_id or uuid7(),
            user_id=book.user_id,
            book_id=book.id,
            page=page,
            previous_page=previous,
            recorded_at=utcnow(),
        )
    )


def _set_page(
    session: Session, book: Book, page: int, today: date, record_id: UUID | None = None
) -> None:
    """R2-R4: records the progress and updates the status and dates."""
    _check_page(book, page)
    if page == book.current_page:
        return
    _record(session, book, page, book.current_page, record_id)
    book.current_page = page
    change = rules.after_page(
        status=book.status,
        page=page,
        total_pages=book.total_pages,
        started_on=book.started_on,
        finished_on=book.finished_on,
        today=today,
    )
    book.status, book.started_on, book.finished_on = (
        change.status,
        change.started_on,
        change.finished_on,
    )


def _apply_status(session: Session, book: Book, status: BookStatus, today: date) -> None:
    """A status chosen by the user fills the empty dates (R3, R4); `read` completes the book."""
    book.status = status
    if status in (BookStatus.READING, BookStatus.READ) and book.started_on is None:
        book.started_on = today
    if status == BookStatus.READ:
        if book.current_page < book.total_pages:
            _record(session, book, book.total_pages, book.current_page)
            book.current_page = book.total_pages
        if book.finished_on is None:
            book.finished_on = today


def create_book(session: Session, user: User, data: BookCreate) -> Book:
    """A book can be added already begun or read: its current page is recorded as the starting
    point (no pages advanced, R7), and the status follows R3 and R4."""
    if data.current_page > data.total_pages:
        raise DomainError(
            "Page is beyond the last page.",
            code="reading.page_out_of_range",
            details={"total_pages": data.total_pages},
        )
    today = _today(timezone_for(session, user.id))
    status = data.status
    page = data.total_pages if status == BookStatus.READ else data.current_page
    if page >= data.total_pages:
        status = BookStatus.READ
    elif page > 0 and status == BookStatus.WANT_TO_READ:
        status = BookStatus.READING
    book = Book(
        id=data.id or uuid7(),
        user_id=user.id,
        title=data.title,
        author=data.author,
        total_pages=data.total_pages,
        current_page=page,
        status=status,
        owned=data.owned,
        started_on=data.started_on or (today if status == BookStatus.READING else None),
        finished_on=data.finished_on or (today if status == BookStatus.READ else None),
    )
    _check_dates(book.started_on, book.finished_on)
    session.add(book)
    session.flush()
    if page:
        _record(session, book, page, page)
    session.commit()
    return book


def update_book(session: Session, user: User, book: Book, data: BookUpdate) -> Book:
    values = data.model_dump(exclude_unset=True)
    today = _today(timezone_for(session, user.id))
    total = values.get("total_pages", book.total_pages)
    if total < book.current_page:
        raise DomainError(
            "The book has fewer pages than the current page.",
            code="reading.page_out_of_range",
            details={"current_page": book.current_page},
        )
    _check_dates(
        values.get("started_on", book.started_on), values.get("finished_on", book.finished_on)
    )
    for name in ("title", "author", "total_pages", "owned", "started_on", "finished_on"):
        if name in values:
            setattr(book, name, values[name])
    if "status" in values and values["status"] != book.status:
        _apply_status(session, book, values["status"], today)
    _check_dates(book.started_on, book.finished_on)
    session.commit()
    return book


def delete_book(session: Session, book: Book) -> None:
    covers.remove(book.id)
    session.delete(book)
    session.commit()


def add_progress(
    session: Session, user: User, book: Book, page: int, record_id: UUID | None = None
) -> Book:
    _set_page(session, book, page, _today(timezone_for(session, user.id)), record_id)
    session.commit()
    return book


def list_progress(session: Session, book: Book) -> list[ProgressRead]:
    records = session.scalars(
        select(ReadingProgress)
        .where(ReadingProgress.book_id == book.id)
        .order_by(ReadingProgress.recorded_at.desc(), ReadingProgress.id.desc())
    )
    return [
        ProgressRead(
            id=r.id,
            page=r.page,
            previous_page=r.previous_page,
            pages=r.pages,
            recorded_at=r.recorded_at,
        )
        for r in records
    ]


def _points(session: Session, book_ids: Iterable[UUID]) -> dict[UUID, list[rules.ProgressPoint]]:
    ids = list(book_ids)
    points: dict[UUID, list[rules.ProgressPoint]] = {book_id: [] for book_id in ids}
    if not ids:
        return points
    rows = session.execute(
        select(
            ReadingProgress.book_id,
            ReadingProgress.recorded_at,
            ReadingProgress.page,
            ReadingProgress.previous_page,
        )
        .where(ReadingProgress.book_id.in_(ids))
        .order_by(ReadingProgress.recorded_at, ReadingProgress.id)
    )
    for book_id, recorded_at, page, previous in rows:
        points[book_id].append(rules.ProgressPoint(recorded_at, page, previous))
    return points


def _notes_counts(session: Session, book_ids: Iterable[UUID]) -> dict[UUID, int]:
    ids = list(book_ids)
    if not ids:
        return {}
    rows = session.execute(
        select(BookNote.book_id, func.count())
        .where(BookNote.book_id.in_(ids))
        .group_by(BookNote.book_id)
    )
    return dict(rows.all())


def book_reads(session: Session, user: User, books: Sequence[Book]) -> list[BookRead]:
    tz = timezone_for(session, user.id)
    now = utcnow()
    today = now.astimezone(tz).date()
    points = _points(session, [book.id for book in books])
    notes = _notes_counts(session, [book.id for book in books])
    reads = []
    for book in books:
        history = points[book.id]
        remaining = book.total_pages - book.current_page
        pages_per_day = (
            rules.pace(history, book.current_page, now)
            if book.status == BookStatus.READING
            else None
        )
        reads.append(
            BookRead(
                id=book.id,
                title=book.title,
                author=book.author,
                total_pages=book.total_pages,
                current_page=book.current_page,
                status=book.status,
                owned=book.owned,
                started_on=book.started_on,
                finished_on=book.finished_on,
                has_cover=book.cover_updated_at is not None,
                cover_updated_at=book.cover_updated_at,
                created_at=book.created_at,
                progress_percent=rules.progress_percent(book.current_page, book.total_pages),
                remaining_pages=remaining,
                pace_pages_per_day=pages_per_day,
                forecast_finish_on=rules.forecast(
                    status=book.status,
                    remaining_pages=remaining,
                    pages_per_day=pages_per_day,
                    today=today,
                ),
                last_progress_at=history[-1].recorded_at if history else None,
                notes_count=notes.get(book.id, 0),
            )
        )
    return reads


def book_read(session: Session, user: User, book: Book) -> BookRead:
    return book_reads(session, user, [book])[0]


def book_detail(session: Session, user: User, book: Book) -> BookDetail:
    read = book_read(session, user, book)
    weeks = rules.weekly_pages(_points(session, [book.id])[book.id], timezone_for(session, user.id))
    return BookDetail(
        **read.model_dump(),
        weekly_pages=[WeekPages(week_start=week, pages=pages) for week, pages in weeks],
    )


BOOK_SORT: dict[str, SortColumn] = {
    "created_at": Book.created_at,
    "title": func.lower(Book.title),
    "author": func.lower(Book.author),
    "finished_on": Book.finished_on,
}


def list_books(
    session: Session,
    user: User,
    page: PageParams,
    *,
    status: BookStatus | None = None,
    owned: bool | None = None,
    q: str | None = None,
    sort: Sort | None = None,
    updated_since: datetime | None = None,
) -> Page[BookRead]:
    stmt = select(Book).where(Book.user_id == user.id)
    if status is not None:
        stmt = stmt.where(Book.status == status)
    if owned is not None:
        stmt = stmt.where(Book.owned.is_(owned))
    if q and (text := q.strip()):
        pattern = f"%{_escape_like(text)}%"
        stmt = stmt.where(
            or_(Book.title.ilike(pattern, escape="\\"), Book.author.ilike(pattern, escape="\\"))
        )
    result = paginate(
        session,
        stmt,
        page,
        sort=sort or Sort("created_at", descending=True),
        sort_columns=BOOK_SORT,
        tiebreaker=(Book.id.desc(),),
        updated_since=updated_since,
    )
    return Page[BookRead](
        items=book_reads(session, user, result.items),
        total=result.total,
        limit=page.limit,
        offset=page.offset,
    )


# ---------------------------------------------------------------- covers (R6)


def set_cover(session: Session, book: Book, data: bytes) -> Book:
    covers.save(book.id, covers.process(data))
    book.cover_updated_at = utcnow()
    session.commit()
    return book


def remove_cover(session: Session, book: Book) -> None:
    covers.remove(book.id)
    book.cover_updated_at = None
    session.commit()


def cover_path(book: Book) -> str:
    path = covers.path_for(book.id)
    if book.cover_updated_at is None or not path.is_file():
        raise NotFoundError()
    return str(path)


# ---------------------------------------------------------------- notes (R10)

_NOTES_ORDER = (BookNote.noted_on.desc(), BookNote.created_at.desc(), BookNote.id.desc())


def get_note(session: Session, book: Book, note_id: UUID) -> BookNote:
    note = session.scalar(
        select(BookNote).where(BookNote.id == note_id, BookNote.book_id == book.id)
    )
    if note is None:
        raise NotFoundError()
    return note


def _note_read(note: BookNote, book: Book) -> NoteRead:
    return NoteRead(
        id=note.id,
        book=_ref(book),
        content=note.content,
        page=note.page,
        noted_on=note.noted_on,
        created_at=note.created_at,
        updated_at=note.updated_at,
    )


def note_read(note: BookNote, book: Book) -> NoteRead:
    return _note_read(note, book)


def list_book_notes(session: Session, book: Book) -> list[NoteRead]:
    notes = session.scalars(
        select(BookNote).where(BookNote.book_id == book.id).order_by(*_NOTES_ORDER)
    )
    return [_note_read(note, book) for note in notes]


def create_note(session: Session, user: User, book: Book, data: NoteCreate) -> BookNote:
    if data.page is not None:
        _check_page(book, data.page)
    note = BookNote(
        id=data.id or uuid7(),
        user_id=user.id,
        book_id=book.id,
        content=data.content,
        page=data.page,
        noted_on=data.noted_on or _today(timezone_for(session, user.id)),
    )
    session.add(note)
    session.commit()
    return note


def update_note(session: Session, book: Book, note: BookNote, data: NoteUpdate) -> BookNote:
    values = data.model_dump(exclude_unset=True)
    if values.get("page") is not None:
        _check_page(book, values["page"])
    for name, value in values.items():
        setattr(note, name, value)
    session.commit()
    return note


def delete_note(session: Session, note: BookNote) -> None:
    session.delete(note)
    session.commit()


def list_notes(
    session: Session,
    user: User,
    page: PageParams,
    *,
    q: str | None = None,
    updated_since: datetime | None = None,
) -> Page[NoteRead]:
    stmt = select(BookNote).where(BookNote.user_id == user.id)
    if q and (text := q.strip()):
        stmt = stmt.where(BookNote.content.ilike(f"%{_escape_like(text)}%", escape="\\"))
    result = paginate(session, stmt.order_by(*_NOTES_ORDER), page, updated_since=updated_since)
    books = {
        book.id: book
        for book in session.scalars(
            select(Book).where(Book.id.in_({note.book_id for note in result.items}))
        )
    }
    return Page[NoteRead](
        items=[_note_read(note, books[note.book_id]) for note in result.items],
        total=result.total,
        limit=page.limit,
        offset=page.offset,
    )


# ---------------------------------------------------------------- overview and Início


def overview(session: Session, user: User) -> ReadingOverview:
    counts: dict[BookStatus, int] = dict(
        session.execute(
            select(Book.status, func.count()).where(Book.user_id == user.id).group_by(Book.status)
        ).all()
    )
    notes = session.scalar(select(func.count()).where(BookNote.user_id == user.id)) or 0
    return ReadingOverview(
        books_count=sum(counts.values()),
        want_to_read_count=counts.get(BookStatus.WANT_TO_READ, 0),
        reading_count=counts.get(BookStatus.READING, 0),
        read_count=counts.get(BookStatus.READ, 0),
        notes_count=notes,
    )


def _shelf_book(book: Book) -> ShelfBook:
    return ShelfBook(
        book=_ref(book),
        status=book.status,
        total_pages=book.total_pages,
        finished_on=book.finished_on,
    )


def build_summary(session: Session, user: User) -> ReadingSummary:
    """The book read most recently, the last one finished and the next one to read."""
    books = list(session.scalars(select(Book).where(Book.user_id == user.id)))
    reading = [book for book in books if book.status == BookStatus.READING]
    last_progress = dict(
        session.execute(
            select(ReadingProgress.book_id, func.max(ReadingProgress.recorded_at))
            .where(ReadingProgress.user_id == user.id)
            .group_by(ReadingProgress.book_id)
        ).all()
    )
    reading.sort(key=lambda book: last_progress.get(book.id) or book.created_at, reverse=True)
    current = reading[0] if reading else None
    read = sorted(
        (b for b in books if b.status == BookStatus.READ and b.finished_on),
        key=lambda b: b.finished_on or date.min,
        reverse=True,
    )
    wanted = sorted(
        (b for b in books if b.status == BookStatus.WANT_TO_READ),
        key=lambda b: b.created_at,
        reverse=True,
    )
    shelf = [_shelf_book(book) for book in (*read[:1], *wanted[:1])]
    return ReadingSummary(
        books_count=len(books),
        current=CurrentBook(
            book=_ref(current),
            current_page=current.current_page,
            total_pages=current.total_pages,
            progress_percent=rules.progress_percent(current.current_page, current.total_pages),
            has_cover=current.cover_updated_at is not None,
            cover_updated_at=current.cover_updated_at,
        )
        if current
        else None,
        shelf=shelf,
    )


def build_activity(session: Session, user: User) -> list[ActivityItem]:
    """R11: progress records (with the pages advanced) and notes, newest first."""
    books = {book.id: book for book in session.scalars(select(Book).where(Book.user_id == user.id))}
    progress = session.scalars(
        select(ReadingProgress)
        .where(
            ReadingProgress.user_id == user.id,
            ReadingProgress.page != ReadingProgress.previous_page,
        )
        .order_by(ReadingProgress.recorded_at.desc())
        .limit(ACTIVITY_LIMIT)
    )
    items = [
        ActivityItem(
            module="reading",
            kind="reading.progress",
            occurred_at=r.recorded_at,
            subject=books[r.book_id].title,
            entity_id=r.book_id,
            data={
                "page": r.page,
                "pages": r.pages,
                "total_pages": books[r.book_id].total_pages,
                "status": books[r.book_id].status.value,
            },
        )
        for r in progress
    ]
    notes = session.scalars(
        select(BookNote)
        .where(BookNote.user_id == user.id)
        .order_by(BookNote.created_at.desc())
        .limit(ACTIVITY_LIMIT)
    )
    items += [
        ActivityItem(
            module="reading",
            kind="reading.note",
            occurred_at=n.created_at,
            subject=books[n.book_id].title,
            entity_id=n.book_id,
            data={"page": n.page, "excerpt": _excerpt(n.content)},
        )
        for n in notes
    ]
    return items


def _excerpt(text: str) -> str:
    single = " ".join(text.split())
    return single if len(single) <= EXCERPT else single[: EXCERPT - 1].rstrip() + "…"
