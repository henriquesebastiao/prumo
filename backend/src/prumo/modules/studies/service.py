"""Business rules of the studies module (docs/dominio.md, E1-E11)."""

from collections.abc import Iterable, Sequence
from datetime import date, datetime, timedelta
from typing import Literal
from uuid import UUID, uuid7
from zoneinfo import ZoneInfo

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from prumo.core.clock import utcnow
from prumo.core.errors import ConflictError, DomainError, NotFoundError
from prumo.core.modules import ActivityItem
from prumo.core.pagination import Page, PageParams, Sort, SortColumn, paginate
from prumo.modules.studies import rules
from prumo.modules.studies.models import (
    PlanBlock,
    StudyArea,
    StudyPlan,
    StudySession,
    Subject,
    Topic,
)
from prumo.modules.studies.schemas import (
    AreaCreate,
    AreaRead,
    AreaUpdate,
    BlockRead,
    BlockWrite,
    DayBlock,
    DayRead,
    DayRow,
    PlanBlocksWrite,
    PlanInForce,
    PlanList,
    PlanRead,
    PlanState,
    StudiesOverview,
    StudiesSummary,
    StudySessionCreate,
    StudySessionRead,
    StudySessionUpdate,
    SubjectCreate,
    SubjectDetail,
    SubjectRead,
    SubjectRef,
    SubjectUpdate,
    SummaryBlock,
    SummaryWeek,
    TopicRead,
    TopicRef,
    WeekMinutes,
    WeekRead,
    WeekSubject,
)
from prumo.system.preferences.service import timezone_for
from prumo.system.users.models import User

ACTIVITY_LIMIT = 10
RECENT_SESSIONS = 10
Archived = Literal["false", "true", "all"]


def _today(tz: ZoneInfo) -> date:
    return utcnow().astimezone(tz).date()


def _escape_like(text: str) -> str:
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _archived_filter[M: (StudyArea, Subject)](
    stmt: Select[M], model: type[M], archived: Archived, updated_since: datetime | None
) -> Select[M]:
    """Archived records are listed on demand, and always in an incremental sync (D41)."""
    if updated_since is not None:
        return stmt
    if archived == "false":
        return stmt.where(model.archived_at.is_(None))
    if archived == "true":
        return stmt.where(model.archived_at.is_not(None))
    return stmt


# ---------------------------------------------------------------- areas


def get_area(session: Session, user: User, area_id: UUID) -> StudyArea:
    area = session.scalar(
        select(StudyArea).where(StudyArea.id == area_id, StudyArea.user_id == user.id)
    )
    if area is None:
        raise NotFoundError()
    return area


def _subject_counts(session: Session, user: User) -> dict[UUID, int]:
    rows = session.execute(
        select(Subject.area_id, func.count())
        .where(Subject.user_id == user.id)
        .group_by(Subject.area_id)
    )
    return dict(rows.all())


def area_read(area: StudyArea, subjects_count: int) -> AreaRead:
    return AreaRead(
        id=area.id,
        name=area.name,
        color=area.color,
        archived_at=area.archived_at,
        subjects_count=subjects_count,
        created_at=area.created_at,
        updated_at=area.updated_at,
    )


def area_reads(session: Session, user: User, areas: Sequence[StudyArea]) -> list[AreaRead]:
    counts = _subject_counts(session, user)
    return [area_read(area, counts.get(area.id, 0)) for area in areas]


def list_areas(
    session: Session,
    user: User,
    page: PageParams,
    *,
    archived: Archived = "false",
    updated_since: datetime | None = None,
) -> Page[AreaRead]:
    stmt = select(StudyArea).where(StudyArea.user_id == user.id)
    stmt = _archived_filter(stmt, StudyArea, archived, updated_since)
    result = paginate(
        session,
        stmt,
        page,
        sort=Sort("name", False),
        sort_columns={"name": func.lower(StudyArea.name)},
        tiebreaker=(StudyArea.id,),
        updated_since=updated_since,
    )
    return Page[AreaRead](
        items=area_reads(session, user, result.items),
        total=result.total,
        limit=result.limit,
        offset=result.offset,
    )


def create_area(session: Session, user: User, data: AreaCreate) -> StudyArea:
    area = StudyArea(id=data.id or uuid7(), user_id=user.id, name=data.name, color=data.color)
    session.add(area)
    session.commit()
    return area


def update_area(session: Session, area: StudyArea, data: AreaUpdate) -> StudyArea:
    for name, value in data.model_dump(exclude_unset=True).items():
        setattr(area, name, value)
    session.commit()
    return area


def set_area_archived(session: Session, area: StudyArea, archived: bool) -> StudyArea:
    area.archived_at = (area.archived_at or utcnow()) if archived else None
    session.commit()
    return area


def delete_area(session: Session, user: User, area: StudyArea) -> None:
    """E9: only without subjects."""
    if _subject_counts(session, user).get(area.id, 0):
        raise DomainError("The area still has subjects.", code="studies.area_in_use")
    session.delete(area)
    session.commit()


# ---------------------------------------------------------------- subjects


def get_subject(session: Session, user: User, subject_id: UUID) -> Subject:
    subject = session.scalar(
        select(Subject).where(Subject.id == subject_id, Subject.user_id == user.id)
    )
    if subject is None:
        raise NotFoundError()
    return subject


def _check_uri(uri: str | None) -> None:
    if uri is not None and not rules.valid_obsidian_uri(uri):
        raise DomainError(
            "Only obsidian:// links are accepted.", code="studies.invalid_obsidian_uri"
        )


def _check_active(subject: Subject) -> None:
    """E9: an archived subject takes no new session nor block."""
    if subject.archived_at is not None:
        raise DomainError("The subject is archived.", code="studies.subject_archived")


def _areas_by_id(session: Session, user: User) -> dict[UUID, StudyArea]:
    return {
        area.id: area
        for area in session.scalars(select(StudyArea).where(StudyArea.user_id == user.id))
    }


def _ref(subject: Subject, areas: dict[UUID, StudyArea]) -> SubjectRef:
    return SubjectRef(id=subject.id, name=subject.name, color=areas[subject.area_id].color)


def _sessions(
    session: Session, user: User, subject_ids: Iterable[UUID] | None = None
) -> list[StudySession]:
    stmt = select(StudySession).where(StudySession.user_id == user.id)
    if subject_ids is not None:
        stmt = stmt.where(StudySession.subject_id.in_(list(subject_ids)))
    return list(session.scalars(stmt.order_by(StudySession.started_at, StudySession.id)))


def _points(sessions: Iterable[StudySession]) -> list[rules.Session]:
    return [rules.Session(s.subject_id, s.started_at, s.duration_minutes) for s in sessions]


def subject_reads(session: Session, user: User, subjects: Sequence[Subject]) -> list[SubjectRead]:
    tz = timezone_for(session, user.id)
    today = _today(tz)
    week = rules.week_start(today)
    areas = _areas_by_id(session, user)
    ids = [subject.id for subject in subjects]
    topics = dict(
        session.execute(
            select(Topic.subject_id, func.count())
            .where(Topic.subject_id.in_(ids))
            .group_by(Topic.subject_id)
        ).all()
    )
    last: dict[UUID, datetime] = {}
    week_minutes: dict[UUID, int] = {}
    for item in _sessions(session, user, ids):
        last[item.subject_id] = max(last.get(item.subject_id, item.started_at), item.started_at)
        day = rules.local_day(item.started_at, tz)
        if week <= day <= today:
            week_minutes[item.subject_id] = (
                week_minutes.get(item.subject_id, 0) + item.duration_minutes
            )
    return [
        SubjectRead(
            id=subject.id,
            area_id=subject.area_id,
            area_name=areas[subject.area_id].name,
            name=subject.name,
            color=areas[subject.area_id].color,
            obsidian_uri=subject.obsidian_uri,
            archived_at=subject.archived_at,
            topics_count=topics.get(subject.id, 0),
            last_session_at=last.get(subject.id),
            minutes_this_week=week_minutes.get(subject.id, 0),
            created_at=subject.created_at,
            updated_at=subject.updated_at,
        )
        for subject in subjects
    ]


def subject_read(session: Session, user: User, subject: Subject) -> SubjectRead:
    return subject_reads(session, user, [subject])[0]


def list_subjects(
    session: Session,
    user: User,
    page: PageParams,
    *,
    area_id: UUID | None = None,
    archived: Archived = "false",
    q: str | None = None,
    sort: Sort | None = None,
    updated_since: datetime | None = None,
) -> Page[SubjectRead]:
    stmt = select(Subject).where(Subject.user_id == user.id)
    stmt = _archived_filter(stmt, Subject, archived, updated_since)
    if area_id is not None:
        stmt = stmt.where(Subject.area_id == area_id)
    if q:
        stmt = stmt.where(Subject.name.ilike(f"%{_escape_like(q)}%", escape="\\"))
    columns: dict[str, SortColumn] = {
        "name": func.lower(Subject.name),
        "created_at": Subject.created_at,
    }
    result = paginate(
        session,
        stmt,
        page,
        sort=sort or Sort("name", False),
        sort_columns=columns,
        tiebreaker=(Subject.id,),
        updated_since=updated_since,
    )
    return Page[SubjectRead](
        items=subject_reads(session, user, result.items),
        total=result.total,
        limit=result.limit,
        offset=result.offset,
    )


def create_subject(session: Session, user: User, data: SubjectCreate) -> Subject:
    get_area(session, user, data.area_id)
    _check_uri(data.obsidian_uri)
    subject = Subject(
        id=data.id or uuid7(),
        user_id=user.id,
        area_id=data.area_id,
        name=data.name,
        obsidian_uri=data.obsidian_uri,
    )
    session.add(subject)
    session.commit()
    return subject


def update_subject(session: Session, user: User, subject: Subject, data: SubjectUpdate) -> Subject:
    values = data.model_dump(exclude_unset=True)
    if "area_id" in values:
        get_area(session, user, values["area_id"])
    if "obsidian_uri" in values:
        _check_uri(values["obsidian_uri"])
    for name, value in values.items():
        setattr(subject, name, value)
    session.commit()
    return subject


def set_subject_archived(session: Session, subject: Subject, archived: bool) -> Subject:
    subject.archived_at = (subject.archived_at or utcnow()) if archived else None
    session.commit()
    return subject


def delete_subject(session: Session, subject: Subject) -> None:
    """E9: with its topics, sessions and blocks (cascaded by the database)."""
    session.delete(subject)
    session.commit()


def subject_detail(session: Session, user: User, subject: Subject) -> SubjectDetail:
    base = subject_read(session, user, subject)
    tz = timezone_for(session, user.id)
    today = _today(tz)
    areas = _areas_by_id(session, user)
    sessions = _sessions(session, user, [subject.id])
    topics_by_id = {topic.id: topic for topic in _topics(session, subject)}
    recent = sorted(sessions, key=lambda s: (s.started_at, s.id), reverse=True)[:RECENT_SESSIONS]
    return SubjectDetail(
        **base.model_dump(),
        topics=topic_reads(session, subject),
        weekly_minutes=[
            WeekMinutes(week_start=week, minutes=minutes)
            for week, minutes in rules.weekly_minutes(_points(sessions), today, tz)
        ],
        recent_sessions=[
            _session_read(item, subject, areas, _topic_of(topics_by_id, item)) for item in recent
        ],
    )


# ---------------------------------------------------------------- topics (E10)


def _topics(session: Session, subject: Subject) -> list[Topic]:
    return list(
        session.scalars(
            select(Topic).where(Topic.subject_id == subject.id).order_by(func.lower(Topic.name))
        )
    )


def topic_reads(session: Session, subject: Subject) -> list[TopicRead]:
    counts = dict(
        session.execute(
            select(StudySession.topic_id, func.count())
            .where(StudySession.subject_id == subject.id, StudySession.topic_id.is_not(None))
            .group_by(StudySession.topic_id)
        ).all()
    )
    return [
        TopicRead(id=t.id, name=t.name, sessions_count=counts.get(t.id, 0), created_at=t.created_at)
        for t in _topics(session, subject)
    ]


def get_topic(session: Session, user: User, topic_id: UUID) -> Topic:
    topic = session.scalar(select(Topic).where(Topic.id == topic_id, Topic.user_id == user.id))
    if topic is None:
        raise NotFoundError()
    return topic


def _resolve_topic(
    session: Session, user: User, subject: Subject, topic_id: UUID | None, topic_name: str | None
) -> Topic | None:
    if topic_id is not None:
        topic = get_topic(session, user, topic_id)
        if topic.subject_id != subject.id:
            raise NotFoundError()
        return topic
    if topic_name:
        existing = session.scalar(
            select(Topic).where(
                Topic.subject_id == subject.id,
                func.lower(Topic.name) == topic_name.strip().lower(),
            )
        )
        if existing is not None:
            return existing
        topic = Topic(user_id=user.id, subject_id=subject.id, name=topic_name.strip())
        session.add(topic)
        session.flush()
        return topic
    return None


def delete_topic(session: Session, topic: Topic) -> None:
    used = session.scalar(
        select(func.count()).select_from(StudySession).where(StudySession.topic_id == topic.id)
    )
    if used:
        raise DomainError("The topic has sessions.", code="studies.topic_in_use")
    session.delete(topic)
    session.commit()


# ---------------------------------------------------------------- plans (E1)


def _plans(session: Session, user: User) -> list[StudyPlan]:
    return list(
        session.scalars(
            select(StudyPlan).where(StudyPlan.user_id == user.id).order_by(StudyPlan.valid_from)
        )
    )


def _blocks(session: Session, plan_ids: Iterable[UUID]) -> dict[UUID, list[PlanBlock]]:
    ids = list(plan_ids)
    blocks: dict[UUID, list[PlanBlock]] = {plan_id: [] for plan_id in ids}
    if ids:
        for block in session.scalars(
            select(PlanBlock)
            .where(PlanBlock.plan_id.in_(ids))
            .order_by(PlanBlock.created_at, PlanBlock.id)
        ):
            blocks[block.plan_id].append(block)
    return blocks


def _rule_blocks(blocks: Iterable[PlanBlock]) -> list[rules.Block]:
    return [
        rules.Block(b.subject_id, tuple(b.weekdays), b.starts_at, b.duration_minutes)
        for b in blocks
    ]


def get_plan(session: Session, user: User, plan_id: UUID) -> StudyPlan:
    plan = session.scalar(
        select(StudyPlan).where(StudyPlan.id == plan_id, StudyPlan.user_id == user.id)
    )
    if plan is None:
        raise NotFoundError()
    return plan


def _plan_state(plan: StudyPlan, plans: Sequence[StudyPlan], today: date) -> PlanState:
    if plan.valid_from > today:
        return "future"
    later = [p for p in plans if today >= p.valid_from > plan.valid_from]
    return "past" if later else "current"


def _plan_read(
    plan: StudyPlan,
    plans: Sequence[StudyPlan],
    blocks: Sequence[PlanBlock],
    subjects: dict[UUID, Subject],
    areas: dict[UUID, StudyArea],
    today: date,
) -> PlanRead:
    following = [p.valid_from for p in plans if p.valid_from > plan.valid_from]
    return PlanRead(
        id=plan.id,
        valid_from=plan.valid_from,
        valid_until=min(following) - timedelta(days=1) if following else None,
        state=_plan_state(plan, plans, today),
        blocks=[
            BlockRead(
                id=b.id,
                subject=_ref(subjects[b.subject_id], areas),
                weekdays=list(b.weekdays),
                starts_at=b.starts_at,
                duration_minutes=b.duration_minutes,
            )
            for b in sorted(
                blocks,
                key=lambda b: (
                    min(b.weekdays),
                    b.starts_at is None,
                    b.starts_at or datetime.min.time(),
                ),
            )
        ],
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )


def _subjects_by_id(session: Session, user: User) -> dict[UUID, Subject]:
    return {s.id: s for s in session.scalars(select(Subject).where(Subject.user_id == user.id))}


def plan_read(session: Session, user: User, plan: StudyPlan) -> PlanRead:
    plans = _plans(session, user)
    return _plan_read(
        plan,
        plans,
        _blocks(session, [plan.id])[plan.id],
        _subjects_by_id(session, user),
        _areas_by_id(session, user),
        _today(timezone_for(session, user.id)),
    )


def list_plans(session: Session, user: User) -> PlanList:
    today = _today(timezone_for(session, user.id))
    plans = _plans(session, user)
    blocks = _blocks(session, [p.id for p in plans])
    subjects = _subjects_by_id(session, user)
    areas = _areas_by_id(session, user)
    return PlanList(
        today=today,
        items=[_plan_read(p, plans, blocks[p.id], subjects, areas, today) for p in reversed(plans)],
    )


def plan_in_force(session: Session, user: User, on: date | None) -> PlanInForce:
    today = _today(timezone_for(session, user.id))
    day = on or today
    plans = _plans(session, user)
    current = [p for p in plans if p.valid_from <= day]
    plan = max(current, key=lambda p: p.valid_from) if current else None
    return PlanInForce(
        on=day,
        today=today,
        plan=None
        if plan is None
        else _plan_read(
            plan,
            plans,
            _blocks(session, [plan.id])[plan.id],
            _subjects_by_id(session, user),
            _areas_by_id(session, user),
            today,
        ),
    )


def _check_blocks(session: Session, user: User, blocks: Sequence[BlockWrite]) -> None:
    subjects = _subjects_by_id(session, user)
    for block in blocks:
        subject = subjects.get(block.subject_id)
        if subject is None:
            raise NotFoundError()
        _check_active(subject)


def _replace_blocks(
    session: Session, user: User, plan: StudyPlan, blocks: Sequence[BlockWrite]
) -> None:
    for existing in _blocks(session, [plan.id])[plan.id]:
        session.delete(existing)
    for block in blocks:
        session.add(
            PlanBlock(
                user_id=user.id,
                plan_id=plan.id,
                subject_id=block.subject_id,
                weekdays=list(block.weekdays),
                starts_at=block.starts_at,
                duration_minutes=block.duration_minutes,
            )
        )


def _check_unlocked(plan: StudyPlan, today: date) -> None:
    if plan.valid_from < today:
        raise DomainError(
            "A plan version already in force cannot change.", code="studies.plan_locked"
        )


def create_plan(
    session: Session,
    user: User,
    valid_from: date,
    blocks: Sequence[BlockWrite],
    plan_id: UUID | None = None,
) -> StudyPlan:
    today = _today(timezone_for(session, user.id))
    if valid_from < today:
        raise DomainError("A plan starts today or later.", code="studies.plan_locked")
    if any(p.valid_from == valid_from for p in _plans(session, user)):
        raise ConflictError(
            "A version already starts on this date.", code="studies.plan_date_taken"
        )
    _check_blocks(session, user, blocks)
    plan = StudyPlan(id=plan_id or uuid7(), user_id=user.id, valid_from=valid_from)
    session.add(plan)
    session.flush()
    _replace_blocks(session, user, plan, blocks)
    session.commit()
    return plan


def update_plan(session: Session, user: User, plan: StudyPlan, data: PlanBlocksWrite) -> StudyPlan:
    _check_unlocked(plan, _today(timezone_for(session, user.id)))
    _check_blocks(session, user, data.blocks)
    _replace_blocks(session, user, plan, data.blocks)
    plan.updated_at = utcnow()
    session.commit()
    return plan


def delete_plan(session: Session, user: User, plan: StudyPlan) -> None:
    _check_unlocked(plan, _today(timezone_for(session, user.id)))
    session.delete(plan)
    session.commit()


# ---------------------------------------------------------------- sessions (E3, E10)


def get_session(session: Session, user: User, session_id: UUID) -> StudySession:
    item = session.scalar(
        select(StudySession).where(StudySession.id == session_id, StudySession.user_id == user.id)
    )
    if item is None:
        raise NotFoundError()
    return item


def _topic_of(topics: dict[UUID, Topic], item: StudySession) -> Topic | None:
    return topics.get(item.topic_id) if item.topic_id else None


def _session_read(
    item: StudySession, subject: Subject, areas: dict[UUID, StudyArea], topic: Topic | None
) -> StudySessionRead:
    return StudySessionRead(
        id=item.id,
        subject=_ref(subject, areas),
        topic=TopicRef(id=topic.id, name=topic.name) if topic else None,
        started_at=item.started_at,
        duration_minutes=item.duration_minutes,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def session_reads(
    session: Session, user: User, items: Sequence[StudySession]
) -> list[StudySessionRead]:
    subjects = _subjects_by_id(session, user)
    areas = _areas_by_id(session, user)
    topic_ids = [item.topic_id for item in items if item.topic_id]
    topics = (
        {t.id: t for t in session.scalars(select(Topic).where(Topic.id.in_(topic_ids)))}
        if topic_ids
        else {}
    )
    return [
        _session_read(item, subjects[item.subject_id], areas, _topic_of(topics, item))
        for item in items
    ]


def session_read(session: Session, user: User, item: StudySession) -> StudySessionRead:
    return session_reads(session, user, [item])[0]


def list_sessions(
    session: Session,
    user: User,
    page: PageParams,
    *,
    subject_id: UUID | None = None,
    from_on: date | None = None,
    to_on: date | None = None,
    sort: Sort | None = None,
    updated_since: datetime | None = None,
) -> Page[StudySessionRead]:
    tz = timezone_for(session, user.id)
    stmt = select(StudySession).where(StudySession.user_id == user.id)
    if subject_id is not None:
        stmt = stmt.where(StudySession.subject_id == subject_id)
    if from_on is not None:
        stmt = stmt.where(
            StudySession.started_at >= datetime.combine(from_on, datetime.min.time(), tz)
        )
    if to_on is not None:
        stmt = stmt.where(
            StudySession.started_at
            < datetime.combine(to_on + timedelta(days=1), datetime.min.time(), tz)
        )
    result = paginate(
        session,
        stmt,
        page,
        sort=sort or Sort("started_at", True),
        sort_columns={"started_at": StudySession.started_at},
        tiebreaker=(StudySession.id.desc(),),
        updated_since=updated_since,
    )
    return Page[StudySessionRead](
        items=session_reads(session, user, result.items),
        total=result.total,
        limit=result.limit,
        offset=result.offset,
    )


def create_session(session: Session, user: User, data: StudySessionCreate) -> StudySession:
    subject = get_subject(session, user, data.subject_id)
    _check_active(subject)
    topic = _resolve_topic(session, user, subject, data.topic_id, data.topic_name)
    item = StudySession(
        id=data.id or uuid7(),
        user_id=user.id,
        subject_id=subject.id,
        topic_id=topic.id if topic else None,
        started_at=data.started_at,
        duration_minutes=data.duration_minutes,
    )
    session.add(item)
    session.commit()
    return item


def update_session(
    session: Session, user: User, item: StudySession, data: StudySessionUpdate
) -> StudySession:
    values = data.model_dump(exclude_unset=True)
    subject = get_subject(session, user, values.get("subject_id", item.subject_id))
    if "subject_id" in values and values["subject_id"] != item.subject_id:
        _check_active(subject)
        item.subject_id = subject.id
        item.topic_id = None
    if "topic_id" in values or "topic_name" in values:
        topic = _resolve_topic(
            session, user, subject, values.get("topic_id"), values.get("topic_name")
        )
        item.topic_id = topic.id if topic else None
    for name in ("started_at", "duration_minutes"):
        if name in values:
            setattr(item, name, values[name])
    session.commit()
    return item


def delete_session(session: Session, item: StudySession) -> None:
    session.delete(item)
    session.commit()


# ---------------------------------------------------------------- day and week (E2-E6)


def _day_rows(
    session: Session,
    user: User,
    days: Sequence[date],
    today: date,
    tz: ZoneInfo,
) -> dict[date, list[rules.SubjectDay]]:
    plans = _plans(session, user)
    blocks = _blocks(session, [p.id for p in plans])
    versions = [(p.valid_from, _rule_blocks(blocks[p.id])) for p in plans]
    subjects = _subjects_by_id(session, user)
    hidden = [s.id for s in subjects.values() if s.archived_at is not None]
    start = datetime.combine(min(days), datetime.min.time(), tz) - timedelta(days=1)
    end = datetime.combine(max(days) + timedelta(days=1), datetime.min.time(), tz) + timedelta(
        days=1
    )
    sessions = _points(
        session.scalars(
            select(StudySession).where(
                StudySession.user_id == user.id,
                StudySession.started_at >= start,
                StudySession.started_at < end,
            )
        )
    )
    return {
        day: rules.subject_days(
            rules.plan_for(versions, day), sessions, day, today, tz, hidden=hidden
        )
        for day in days
    }


def _day_read(
    day: date, rows: Sequence[rules.SubjectDay], today: date, refs: dict[UUID, SubjectRef]
) -> DayRead:
    return DayRead(
        on=day,
        today=today,
        is_today=day == today,
        rows=[
            DayRow(
                subject=refs[row.subject_id],
                goal_minutes=row.goal_minutes,
                done_minutes=row.done_minutes,
                status=row.status,
                blocks=[
                    DayBlock(starts_at=b.starts_at, duration_minutes=b.duration_minutes)
                    for b in row.blocks
                ],
            )
            for row in rows
        ],
        done_minutes=sum(row.done_minutes for row in rows),
        planned_minutes=sum(row.goal_minutes for row in rows),
        met=rules.day_met(rows),
    )


def _refs(session: Session, user: User) -> dict[UUID, SubjectRef]:
    areas = _areas_by_id(session, user)
    return {s.id: _ref(s, areas) for s in _subjects_by_id(session, user).values()}


def day(session: Session, user: User, on: date | None) -> DayRead:
    tz = timezone_for(session, user.id)
    today = _today(tz)
    target = on or today
    rows = _day_rows(session, user, [target], today, tz)[target]
    return _day_read(target, rows, today, _refs(session, user))


def week(session: Session, user: User, start: date | None) -> WeekRead:
    tz = timezone_for(session, user.id)
    today = _today(tz)
    first = rules.week_start(start or today)
    days = [first + timedelta(days=i) for i in range(7)]
    rows = _day_rows(session, user, days, today, tz)
    totals = rules.week_totals(rows, today)
    refs = _refs(session, user)
    by_subject: dict[UUID, list[int]] = {}
    for day_rows in rows.values():
        for row in day_rows:
            minutes = by_subject.setdefault(row.subject_id, [0, 0])
            minutes[0] += row.done_minutes
            minutes[1] += row.goal_minutes
    latest = rules.week_start(today) + timedelta(weeks=1)
    return WeekRead(
        start=first,
        end=days[-1],
        today=today,
        days=[_day_read(d, rows[d], today, refs) for d in days],
        days_met=totals.days_met,
        days_planned=totals.days_planned,
        minutes_done=totals.minutes_done,
        minutes_planned=totals.minutes_planned,
        by_subject=sorted(
            (
                WeekSubject(subject=refs[sid], minutes_done=done, minutes_planned=planned)
                for sid, (done, planned) in by_subject.items()
            ),
            key=lambda item: (-item.minutes_planned, item.subject.name.lower()),
        ),
        previous_start=first - timedelta(weeks=1),
        next_start=first + timedelta(weeks=1) if first < latest else None,
    )


def overview(session: Session, user: User) -> StudiesOverview:
    tz = timezone_for(session, user.id)
    today = _today(tz)
    month_start = datetime.combine(today.replace(day=1), datetime.min.time(), tz)
    counts = session.execute(
        select(
            func.count(StudySession.id), func.coalesce(func.sum(StudySession.duration_minutes), 0)
        ).where(StudySession.user_id == user.id, StudySession.started_at >= month_start)
    ).one()
    return StudiesOverview(
        areas_count=session.scalar(
            select(func.count())
            .select_from(StudyArea)
            .where(StudyArea.user_id == user.id, StudyArea.archived_at.is_(None))
        )
        or 0,
        subjects_count=session.scalar(
            select(func.count())
            .select_from(Subject)
            .where(Subject.user_id == user.id, Subject.archived_at.is_(None))
        )
        or 0,
        sessions_this_month=counts[0],
        minutes_this_month=int(counts[1]),
    )


# ---------------------------------------------------------------- Início (E11)


def build_summary(session: Session, user: User) -> StudiesSummary:
    tz = timezone_for(session, user.id)
    today = _today(tz)
    first = rules.week_start(today)
    days = [first + timedelta(days=i) for i in range(7)]
    rows = _day_rows(session, user, days, today, tz)
    totals = rules.week_totals(rows, today)
    refs = _refs(session, user)
    blocks = []
    for row in rows[today]:
        if row.blocks:
            for block in row.blocks:
                blocks.append(
                    SummaryBlock(
                        subject=refs[row.subject_id],
                        starts_at=block.starts_at,
                        goal_minutes=row.goal_minutes,
                        done_minutes=row.done_minutes,
                        status=row.status,
                    )
                )
        else:
            blocks.append(
                SummaryBlock(
                    subject=refs[row.subject_id],
                    starts_at=None,
                    goal_minutes=0,
                    done_minutes=row.done_minutes,
                    status=row.status,
                )
            )
    return StudiesSummary(
        today=today,
        blocks_today=blocks,
        done_minutes_today=sum(row.done_minutes for row in rows[today]),
        planned_minutes_today=sum(row.goal_minutes for row in rows[today]),
        week=SummaryWeek(
            days_met=totals.days_met,
            days_planned=totals.days_planned,
            minutes_done=totals.minutes_done,
            minutes_planned=totals.minutes_planned,
        ),
    )


def build_activity(session: Session, user: User) -> list[ActivityItem]:
    """E11: the latest sessions."""
    items = list(
        session.scalars(
            select(StudySession)
            .where(StudySession.user_id == user.id)
            .order_by(StudySession.started_at.desc(), StudySession.id.desc())
            .limit(ACTIVITY_LIMIT)
        )
    )
    reads = session_reads(session, user, items)
    return [
        ActivityItem(
            module="studies",
            kind="studies.session",
            occurred_at=read.started_at,
            subject=read.subject.name,
            entity_id=read.subject.id,
            data={
                "session_id": str(read.id),
                "topic": read.topic.name if read.topic else None,
                "duration_minutes": read.duration_minutes,
                "color": read.subject.color,
            },
        )
        for read in reads
    ]
