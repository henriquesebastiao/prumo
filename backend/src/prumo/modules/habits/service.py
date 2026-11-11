"""Business rules of the habits module (docs/dominio.md, H1-H9)."""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any, Literal
from uuid import UUID, uuid7
from zoneinfo import ZoneInfo

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from prumo.core.clock import utcnow
from prumo.core.errors import ConflictError, DomainError, NotFoundError
from prumo.core.pagination import Page, PageParams, Sort, paginate
from prumo.modules.habits import rules
from prumo.modules.habits.models import Habit, HabitEntry, HabitFrequency, HabitPause, Relapse
from prumo.modules.habits.schemas import (
    FrequencyState,
    HabitCalendar,
    HabitCalendarDay,
    HabitCreate,
    HabitDetail,
    HabitEntryRead,
    HabitEntryWrite,
    HabitFrequencyCreate,
    HabitFrequencyFields,
    HabitFrequencyRead,
    HabitFrequencyUpdate,
    HabitPauseCreate,
    HabitPauseRead,
    HabitPauseUpdate,
    HabitRead,
    HabitRef,
    HabitsSummary,
    HabitsSummaryQuit,
    HabitsToday,
    HabitTodayItem,
    HabitTodayState,
    HabitUpdate,
    HabitWeek,
    RelapseCreate,
    RelapseRead,
)
from prumo.system.preferences.service import timezone_for
from prumo.system.users.models import User

Archived = Literal["false", "true", "all"]
RECENT_RELAPSES = 20
SUMMARY_PENDING = 3


def _today(tz: ZoneInfo) -> date:
    return utcnow().astimezone(tz).date()


def _error(message: str, code: str) -> DomainError:
    return DomainError(message, code=code)


def _require_build(habit: Habit) -> None:
    if habit.kind != "build":
        raise _error("Only habits to practice take this.", "habits.not_build")


def _require_quit(habit: Habit) -> None:
    if habit.kind != "quit":
        raise _error("Only habits to quit take relapses.", "habits.not_quit")


# ---------------------------------------------------------------- loading


@dataclass
class _Records:
    frequencies: dict[UUID, list[HabitFrequency]]
    pauses: dict[UUID, list[HabitPause]]
    entries: dict[UUID, dict[date, int]]
    relapses: dict[UUID, list[Relapse]]


def _group[T: (HabitFrequency, HabitPause, Relapse)](items: Iterable[T]) -> dict[UUID, list[T]]:
    found: dict[UUID, list[T]] = {}
    for item in items:
        found.setdefault(item.habit_id, []).append(item)
    return found


def _records(session: Session, habits: Sequence[Habit]) -> _Records:
    ids = [h.id for h in habits]
    if not ids:
        return _Records({}, {}, {}, {})
    frequencies = _group(
        session.scalars(select(HabitFrequency).where(HabitFrequency.habit_id.in_(ids)))
    )
    pauses = _group(session.scalars(select(HabitPause).where(HabitPause.habit_id.in_(ids))))
    relapses = _group(session.scalars(select(Relapse).where(Relapse.habit_id.in_(ids))))
    entries: dict[UUID, dict[date, int]] = {}
    for habit_id, day, value in session.execute(
        select(HabitEntry.habit_id, HabitEntry.day, HabitEntry.value).where(
            HabitEntry.habit_id.in_(ids)
        )
    ):
        entries.setdefault(habit_id, {})[day] = value
    return _Records(frequencies, pauses, entries, relapses)


def _rule_frequency(frequency: HabitFrequency) -> rules.Frequency:
    return rules.Frequency(
        valid_from=frequency.valid_from,
        kind=rules.HabitFrequencyKind(frequency.kind),
        times_per_week=frequency.times_per_week,
        weekdays=tuple(frequency.weekdays or ()),
    )


def _rule_habit(habit: Habit, records: _Records) -> rules.Habit:
    return rules.Habit(
        started_on=habit.started_on,
        measure=habit.measure or "check",
        target_value=habit.target_value,
        frequencies=tuple(_rule_frequency(f) for f in records.frequencies.get(habit.id, ())),
        pauses=tuple(rules.Pause(p.starts_on, p.ends_on) for p in records.pauses.get(habit.id, ())),
        entries=records.entries.get(habit.id, {}),
    )


def _frequency_reads(
    frequencies: Iterable[HabitFrequency], today: date
) -> list[HabitFrequencyRead]:
    """Newest first, each with the day before the next version and its state (H2)."""
    ordered = sorted(frequencies, key=lambda f: f.valid_from)
    in_force = next((f for f in reversed(ordered) if f.valid_from <= today), None)
    reads = []
    for index, frequency in enumerate(ordered):
        following = ordered[index + 1] if index + 1 < len(ordered) else None
        state: FrequencyState
        if frequency is in_force:
            state = "current"
        elif frequency.valid_from > today:
            state = "future"
        else:
            state = "past"
        reads.append(
            HabitFrequencyRead(
                id=frequency.id,
                valid_from=frequency.valid_from,
                valid_until=following.valid_from - timedelta(days=1) if following else None,
                state=state,
                kind=rules.HabitFrequencyKind(frequency.kind),
                times_per_week=frequency.times_per_week,
                weekdays=frequency.weekdays,
            )
        )
    return list(reversed(reads))


@dataclass(frozen=True)
class _Moment:
    tz: ZoneInfo
    today: date
    now: datetime


def _moment(session: Session, user: User) -> _Moment:
    tz = timezone_for(session, user.id)
    now = utcnow().astimezone(tz)
    return _Moment(tz, now.date(), now)


def _habit_read(habit: Habit, records: _Records, moment: _Moment) -> HabitRead:
    values: dict[str, Any] = {
        "id": habit.id,
        "name": habit.name,
        "kind": habit.kind,
        "color": habit.color,
        "icon": habit.icon,
        "started_on": habit.started_on,
        "measure": habit.measure,
        "target_value": habit.target_value,
        "unit": habit.unit,
        "archived_at": habit.archived_at,
        "created_at": habit.created_at,
        "updated_at": habit.updated_at,
        "frequency": None,
        "paused": False,
        "rate_percent": None,
        "current_streak": None,
        "best_streak": None,
        "streak_unit": None,
        "week": None,
        "today": None,
        "clean_since": None,
        "clean_days": None,
        "best_clean_days": None,
        "relapses_30d": None,
    }
    if habit.kind == "quit":
        clean = rules.clean(
            habit.started_on,
            (r.occurred_at for r in records.relapses.get(habit.id, ())),
            moment.now,
            moment.tz,
        )
        values.update(
            clean_since=clean.since.astimezone(UTC),
            clean_days=clean.days,
            best_clean_days=clean.best_days,
            relapses_30d=clean.relapses_30d,
        )
        return HabitRead.model_validate(values)
    rule = _rule_habit(habit, records)
    found = rules.units(rule, moment.today)
    current, best = rules.streaks(found)
    frequency = rules.frequency_for(rule.frequencies, moment.today)
    reads = _frequency_reads(records.frequencies.get(habit.id, ()), moment.today)
    week = rules.current_week(found, moment.today)
    weekly = frequency is not None and frequency.kind == rules.HabitFrequencyKind.WEEKLY
    values.update(
        frequency=next((f for f in reads if f.state == "current"), None),
        paused=rules.paused(rule.pauses, moment.today),
        rate_percent=rules.rate_percent(found, frequency, moment.today),
        current_streak=current,
        best_streak=best,
        streak_unit="week" if weekly else "day",
        week=HabitWeek(done=week.done, target=week.required) if week and weekly else None,
        today=HabitTodayState(
            scheduled=rules.scheduled_today(found, moment.today) is not None,
            done=rules.day_met(rule, moment.today),
            value=rule.entries.get(moment.today),
        ),
    )
    return HabitRead.model_validate(values)


def habit_reads(session: Session, user: User, habits: Sequence[Habit]) -> list[HabitRead]:
    records = _records(session, habits)
    moment = _moment(session, user)
    return [_habit_read(habit, records, moment) for habit in habits]


def habit_read(session: Session, user: User, habit: Habit) -> HabitRead:
    return habit_reads(session, user, [habit])[0]


# ---------------------------------------------------------------- habits


def get_habit(session: Session, user: User, habit_id: UUID) -> Habit:
    habit = session.scalar(select(Habit).where(Habit.id == habit_id, Habit.user_id == user.id))
    if habit is None:
        raise NotFoundError()
    return habit


def _archived_filter(
    stmt: Select[Habit], archived: Archived, updated_since: datetime | None
) -> Select[Habit]:
    """Archived habits are listed on demand, and always in an incremental sync (D41)."""
    if updated_since is not None:
        return stmt
    if archived == "false":
        return stmt.where(Habit.archived_at.is_(None))
    if archived == "true":
        return stmt.where(Habit.archived_at.is_not(None))
    return stmt


def list_habits(
    session: Session,
    user: User,
    page: PageParams,
    *,
    kind: Literal["build", "quit"] | None = None,
    archived: Archived = "false",
    updated_since: datetime | None = None,
) -> Page[HabitRead]:
    stmt = select(Habit).where(Habit.user_id == user.id)
    if kind is not None:
        stmt = stmt.where(Habit.kind == kind)
    stmt = _archived_filter(stmt, archived, updated_since)
    result = paginate(
        session,
        stmt,
        page,
        sort=Sort("name", False),
        sort_columns={"name": func.lower(Habit.name)},
        tiebreaker=(Habit.id,),
        updated_since=updated_since,
    )
    return Page[HabitRead](
        items=habit_reads(session, user, result.items),
        total=result.total,
        limit=result.limit,
        offset=result.offset,
    )


def _check_measure(measure: str | None, target_value: int | None, unit: str | None) -> None:
    if measure == "quantity" and (target_value is None or unit is None):
        raise _error("A quantity needs a target and a unit.", "habits.invalid_measure")


def create_habit(session: Session, user: User, data: HabitCreate) -> Habit:
    today = _today(timezone_for(session, user.id))
    started_on = data.started_on or today
    if started_on > today:
        raise _error("A habit starts today or before.", "habits.future_date")
    habit = Habit(
        id=data.id or uuid7(),
        user_id=user.id,
        name=data.name,
        kind=data.kind,
        color=data.color,
        icon=data.icon,
        started_on=started_on,
    )
    if data.kind == "build":
        habit.measure = data.measure or "check"
        if habit.measure == "quantity":
            _check_measure(habit.measure, data.target_value, data.unit)
            habit.target_value = data.target_value
            habit.unit = data.unit
    session.add(habit)
    session.flush()
    if data.kind == "build":
        frequency = data.frequency or HabitFrequencyFields(kind=rules.HabitFrequencyKind.DAILY)
        session.add(_frequency(user, habit, started_on, frequency))
    session.commit()
    return habit


def update_habit(session: Session, user: User, habit: Habit, data: HabitUpdate) -> Habit:
    values = data.model_dump(exclude_unset=True)
    if ("target_value" in values or "unit" in values) and habit.measure != "quantity":
        raise _error("Only a quantity has a target and a unit.", "habits.invalid_measure")
    started_on = values.get("started_on")
    if started_on is not None:
        if started_on > _today(timezone_for(session, user.id)):
            raise _error("A habit starts today or before.", "habits.future_date")
        if habit.kind == "build":
            first = session.scalar(
                select(HabitFrequency)
                .where(HabitFrequency.habit_id == habit.id)
                .order_by(HabitFrequency.valid_from)
                .limit(1)
            )
            # The first version follows an earlier start: every day from the start is covered.
            if first is not None and started_on < first.valid_from:
                first.valid_from = started_on
    for name, value in values.items():
        setattr(habit, name, value)
    session.commit()
    return habit


def set_archived(session: Session, habit: Habit, archived: bool) -> Habit:
    habit.archived_at = (habit.archived_at or utcnow()) if archived else None
    session.commit()
    return habit


def delete_habit(session: Session, habit: Habit) -> None:
    session.delete(habit)
    session.commit()


def habit_detail(session: Session, user: User, habit: Habit) -> HabitDetail:
    records = _records(session, [habit])
    moment = _moment(session, user)
    read = _habit_read(habit, records, moment)
    pauses = sorted(records.pauses.get(habit.id, ()), key=lambda p: p.starts_on, reverse=True)
    relapses = sorted(
        records.relapses.get(habit.id, ()), key=lambda r: r.occurred_at, reverse=True
    )[:RECENT_RELAPSES]
    return HabitDetail(
        **read.model_dump(),
        frequencies=_frequency_reads(records.frequencies.get(habit.id, ()), moment.today),
        pauses=[_pause_read(p) for p in pauses],
        relapses=[_relapse_read(r) for r in relapses],
    )


def _month_of(day: date) -> str:
    return f"{day.year:04d}-{day.month:02d}"


def _shift_month(first: date, months: int) -> date:
    index = first.year * 12 + first.month - 1 + months
    return date(index // 12, index % 12 + 1, 1)


def calendar(session: Session, user: User, habit: Habit, month: str | None) -> HabitCalendar:
    """Each day of a month with its status (done, partial, missed, pending, paused, unscheduled)."""
    _require_build(habit)
    moment = _moment(session, user)
    current = moment.today.replace(day=1)
    first = date(int(month[:4]), int(month[5:7]), 1) if month else current
    following = _shift_month(first, 1)
    rule = _rule_habit(habit, _records(session, [habit]))
    days = []
    day = first
    while day < following:
        days.append(
            HabitCalendarDay(
                on=day,
                status=rules.day_status(rule, day, moment.today),
                value=rule.entries.get(day),
            )
        )
        day += timedelta(days=1)
    return HabitCalendar(
        month=_month_of(first),
        today=moment.today,
        days=days,
        previous_month=_month_of(_shift_month(first, -1)),
        next_month=_month_of(following) if following <= current else None,
    )


# ---------------------------------------------------------------- frequencies (H2)


def _frequency(
    user: User,
    habit: Habit,
    valid_from: date,
    data: HabitFrequencyFields,
    frequency_id: UUID | None = None,
) -> HabitFrequency:
    return HabitFrequency(
        id=frequency_id or uuid7(),
        user_id=user.id,
        habit_id=habit.id,
        valid_from=valid_from,
        kind=data.kind.value,
        times_per_week=data.times_per_week,
        weekdays=data.weekdays,
    )


def get_frequency(session: Session, user: User, frequency_id: UUID) -> HabitFrequency:
    frequency = session.scalar(
        select(HabitFrequency).where(
            HabitFrequency.id == frequency_id, HabitFrequency.user_id == user.id
        )
    )
    if frequency is None:
        raise NotFoundError()
    return frequency


def _locked(message: str) -> DomainError:
    return _error(message, "habits.frequency_locked")


def create_frequency(
    session: Session, user: User, habit: Habit, data: HabitFrequencyCreate
) -> HabitFrequency:
    """H2: a new version from `valid_from`, today or later."""
    _require_build(habit)
    if data.valid_from < _today(timezone_for(session, user.id)):
        raise _locked("A frequency starts today or later.")
    taken = session.scalar(
        select(HabitFrequency.id).where(
            HabitFrequency.habit_id == habit.id, HabitFrequency.valid_from == data.valid_from
        )
    )
    if taken is not None:
        raise ConflictError(
            "A version already starts on this date.", code="habits.frequency_date_taken"
        )
    frequency = _frequency(user, habit, data.valid_from, data, data.id)
    session.add(frequency)
    session.commit()
    return frequency


def update_frequency(
    session: Session, user: User, frequency: HabitFrequency, data: HabitFrequencyUpdate
) -> HabitFrequency:
    if frequency.valid_from < _today(timezone_for(session, user.id)):
        raise _locked("A version already in force cannot change.")
    frequency.kind = data.kind.value
    frequency.times_per_week = data.times_per_week
    frequency.weekdays = data.weekdays
    session.commit()
    return frequency


def delete_frequency(session: Session, user: User, frequency: HabitFrequency) -> None:
    """A version not yet in force; never the first one (every day from the start has one)."""
    if frequency.valid_from < _today(timezone_for(session, user.id)):
        raise _locked("A version already in force cannot change.")
    first = session.scalar(
        select(func.min(HabitFrequency.valid_from)).where(
            HabitFrequency.habit_id == frequency.habit_id
        )
    )
    if frequency.valid_from == first:
        raise _locked("The first version stays.")
    session.delete(frequency)
    session.commit()


# ---------------------------------------------------------------- entries (H1, H3)


def _check_day(habit: Habit, on: date, today: date) -> None:
    """H3: from the habit's start to today, in the user's zone."""
    if on > today:
        raise _error("A day in the future cannot be marked.", "habits.future_date")
    if on < habit.started_on:
        raise _error("The habit had not started on this day.", "habits.before_start")


def put_entry(session: Session, user: User, habit: Habit, on: date, data: HabitEntryWrite) -> Habit:
    """Marks a day, or changes its value (idempotent by habit and day, D47)."""
    _require_build(habit)
    _check_day(habit, on, _today(timezone_for(session, user.id)))
    value = data.value if habit.measure == "quantity" else 1
    entry = session.scalar(
        select(HabitEntry).where(HabitEntry.habit_id == habit.id, HabitEntry.day == on)
    )
    if entry is None:
        session.add(HabitEntry(id=uuid7(), user_id=user.id, habit_id=habit.id, day=on, value=value))
    elif entry.value != value:
        entry.value = value
    session.commit()
    return habit


def delete_entry(session: Session, user: User, habit: Habit, on: date) -> Habit:
    """Unmarks a day; a day without an entry stays as it is."""
    _require_build(habit)
    entry = session.scalar(
        select(HabitEntry).where(HabitEntry.habit_id == habit.id, HabitEntry.day == on)
    )
    if entry is not None:
        session.delete(entry)
        session.commit()
    return habit


def _entry_read(entry: HabitEntry) -> HabitEntryRead:
    return HabitEntryRead(
        id=entry.id,
        habit_id=entry.habit_id,
        on=entry.day,
        value=entry.value,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    )


def list_entries(
    session: Session,
    user: User,
    page: PageParams,
    *,
    habit_id: UUID | None = None,
    from_on: date | None = None,
    to_on: date | None = None,
    updated_since: datetime | None = None,
) -> Page[HabitEntryRead]:
    stmt = select(HabitEntry).where(HabitEntry.user_id == user.id)
    if habit_id is not None:
        stmt = stmt.where(HabitEntry.habit_id == habit_id)
    if from_on is not None:
        stmt = stmt.where(HabitEntry.day >= from_on)
    if to_on is not None:
        stmt = stmt.where(HabitEntry.day <= to_on)
    result = paginate(
        session,
        stmt,
        page,
        sort=Sort("on", True),
        sort_columns={"on": HabitEntry.day},
        tiebreaker=(HabitEntry.id,),
        updated_since=updated_since,
    )
    return Page[HabitEntryRead](
        items=[_entry_read(e) for e in result.items],
        total=result.total,
        limit=result.limit,
        offset=result.offset,
    )


# ---------------------------------------------------------------- pauses


def _pause_read(pause: HabitPause) -> HabitPauseRead:
    return HabitPauseRead(
        id=pause.id,
        starts_on=pause.starts_on,
        ends_on=pause.ends_on,
        created_at=pause.created_at,
        updated_at=pause.updated_at,
    )


def pause_read(pause: HabitPause) -> HabitPauseRead:
    return _pause_read(pause)


def get_pause(session: Session, user: User, pause_id: UUID) -> HabitPause:
    pause = session.scalar(
        select(HabitPause).where(HabitPause.id == pause_id, HabitPause.user_id == user.id)
    )
    if pause is None:
        raise NotFoundError()
    return pause


def _check_overlap(
    session: Session, habit_id: UUID, starts_on: date, ends_on: date | None, skip: UUID | None
) -> None:
    """H8: pauses don't overlap; an open pause runs on with no end."""
    for other in session.scalars(select(HabitPause).where(HabitPause.habit_id == habit_id)):
        if other.id == skip:
            continue
        ends_first = ends_on is not None and ends_on < other.starts_on
        starts_after = other.ends_on is not None and starts_on > other.ends_on
        if not (ends_first or starts_after):
            raise _error("The pause overlaps another one.", "habits.pause_overlap")


def create_pause(session: Session, user: User, habit: Habit, data: HabitPauseCreate) -> HabitPause:
    _require_build(habit)
    _check_overlap(session, habit.id, data.starts_on, data.ends_on, None)
    pause = HabitPause(
        id=data.id or uuid7(),
        user_id=user.id,
        habit_id=habit.id,
        starts_on=data.starts_on,
        ends_on=data.ends_on,
    )
    session.add(pause)
    session.commit()
    return pause


def update_pause(session: Session, pause: HabitPause, data: HabitPauseUpdate) -> HabitPause:
    values = data.model_dump(exclude_unset=True)
    starts_on = values.get("starts_on", pause.starts_on)
    ends_on = values.get("ends_on", pause.ends_on)
    if ends_on is not None and ends_on < starts_on:
        raise DomainError("A pause ends on or after it starts.", code="validation_error")
    _check_overlap(session, pause.habit_id, starts_on, ends_on, pause.id)
    pause.starts_on = starts_on
    pause.ends_on = ends_on
    session.commit()
    return pause


def delete_pause(session: Session, pause: HabitPause) -> None:
    session.delete(pause)
    session.commit()


# ---------------------------------------------------------------- relapses (H7)


def _relapse_read(relapse: Relapse) -> RelapseRead:
    return RelapseRead(
        id=relapse.id,
        occurred_at=relapse.occurred_at,
        note=relapse.note,
        created_at=relapse.created_at,
        updated_at=relapse.updated_at,
    )


def get_relapse(session: Session, user: User, relapse_id: UUID) -> Relapse:
    relapse = session.scalar(
        select(Relapse).where(Relapse.id == relapse_id, Relapse.user_id == user.id)
    )
    if relapse is None:
        raise NotFoundError()
    return relapse


def create_relapse(session: Session, user: User, habit: Habit, data: RelapseCreate) -> Relapse:
    _require_quit(habit)
    tz = timezone_for(session, user.id)
    if data.occurred_at > utcnow():
        raise _error("A relapse cannot be in the future.", "habits.future_date")
    if data.occurred_at < rules.start_moment(habit.started_on, tz):
        raise _error("The habit had not started then.", "habits.before_start")
    relapse = Relapse(
        id=data.id or uuid7(),
        user_id=user.id,
        habit_id=habit.id,
        occurred_at=data.occurred_at,
        note=data.note,
    )
    session.add(relapse)
    session.commit()
    return relapse


def delete_relapse(session: Session, relapse: Relapse) -> None:
    session.delete(relapse)
    session.commit()


# ---------------------------------------------------------------- today and Início (H9)


def _ref(habit: Habit) -> HabitRef:
    return HabitRef.model_validate(
        {
            "id": habit.id,
            "name": habit.name,
            "color": habit.color,
            "icon": habit.icon,
            "measure": habit.measure,
            "target_value": habit.target_value,
            "unit": habit.unit,
        }
    )


def _active(session: Session, user: User, kind: str) -> list[Habit]:
    return list(
        session.scalars(
            select(Habit)
            .where(Habit.user_id == user.id, Habit.kind == kind, Habit.archived_at.is_(None))
            .order_by(func.lower(Habit.name), Habit.id)
        )
    )


def today(session: Session, user: User) -> HabitsToday:
    """The `build` habits that ask something of today (H2): their day, or the week in progress."""
    habits = _active(session, user, "build")
    records = _records(session, habits)
    moment = _moment(session, user)
    items = []
    for habit in habits:
        rule = _rule_habit(habit, records)
        found = rules.units(rule, moment.today)
        unit = rules.scheduled_today(found, moment.today)
        if unit is None:
            continue
        done = rules.day_met(rule, moment.today)
        week = HabitWeek(done=unit.done, target=unit.required) if unit.weekly else None
        items.append(
            HabitTodayItem(
                habit=_ref(habit),
                done=done,
                value=rule.entries.get(moment.today),
                week=week,
                settled=done or (unit.weekly and unit.met),
            )
        )
    return HabitsToday(
        today=moment.today,
        items=items,
        done=sum(1 for i in items if i.settled),
        scheduled=len(items),
    )


def build_summary(session: Session, user: User) -> HabitsSummary:
    day = today(session, user)
    pending = [item.habit for item in day.items if not item.settled]
    quit_habits = _active(session, user, "quit")
    reads = habit_reads(session, user, quit_habits)
    return HabitsSummary(
        today=day.today,
        done_today=day.done,
        scheduled_today=day.scheduled,
        pending=pending[:SUMMARY_PENDING],
        pending_more=max(0, len(pending) - SUMMARY_PENDING),
        quit=[
            HabitsSummaryQuit(
                id=read.id,
                name=read.name,
                color=read.color,
                icon=read.icon,
                clean_days=read.clean_days or 0,
            )
            for read in reads
        ],
    )
