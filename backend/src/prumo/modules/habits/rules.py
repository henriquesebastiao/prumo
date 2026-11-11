"""Pure calculations of the habits rules (no database). See docs/dominio.md, H1-H7."""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from enum import StrEnum
from itertools import pairwise
from zoneinfo import ZoneInfo

RATE_DAYS = 30
RATE_WEEKS = 4
RELAPSE_WINDOW = timedelta(days=30)


class HabitFrequencyKind(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    WEEKDAYS = "weekdays"


class CalendarStatus(StrEnum):
    """A day of a habit's calendar."""

    DONE = "done"
    PARTIAL = "partial"
    MISSED = "missed"
    PENDING = "pending"
    PAUSED = "paused"
    UNSCHEDULED = "unscheduled"
    FUTURE = "future"


@dataclass(frozen=True)
class Frequency:
    valid_from: date
    kind: HabitFrequencyKind
    times_per_week: int | None = None
    weekdays: tuple[int, ...] = ()


@dataclass(frozen=True)
class Pause:
    starts_on: date
    ends_on: date | None


@dataclass(frozen=True)
class Habit:
    """What the rules need of a `build` habit."""

    started_on: date
    measure: str  # check | quantity
    target_value: int | None
    frequencies: tuple[Frequency, ...]
    pauses: tuple[Pause, ...]
    entries: Mapping[date, int]


@dataclass(frozen=True)
class Unit:
    """A scheduled unit (H2): a day, or a week in `weekly`."""

    weekly: bool
    first: date
    last: date
    required: int
    done: int
    closed: bool

    @property
    def met(self) -> bool:
        return self.done >= self.required


def week_start(day: date) -> date:
    return day - timedelta(days=day.weekday())


def frequency_for(frequencies: Iterable[Frequency], day: date) -> Frequency | None:
    """H2: the version in force on `day` (the latest `valid_from` <= day)."""
    chosen: Frequency | None = None
    for frequency in frequencies:
        if frequency.valid_from <= day and (
            chosen is None or frequency.valid_from > chosen.valid_from
        ):
            chosen = frequency
    return chosen


def paused(pauses: Iterable[Pause], day: date) -> bool:
    return any(p.starts_on <= day and (p.ends_on is None or day <= p.ends_on) for p in pauses)


def day_met(habit: Habit, day: date) -> bool:
    """H1: `check` has an entry; `quantity` reached its target."""
    value = habit.entries.get(day)
    if value is None:
        return False
    if habit.measure == "quantity":
        return value >= (habit.target_value or 1)
    return True


def _scheduled_on(frequency: Frequency, day: date) -> bool:
    if frequency.kind == HabitFrequencyKind.DAILY:
        return True
    if frequency.kind == HabitFrequencyKind.WEEKDAYS:
        return day.weekday() in frequency.weekdays
    return False


def units(habit: Habit, today: date) -> list[Unit]:
    """H2: the scheduled units from the start to today, oldest first.

    Days in a pause, before the start or in the future don't count. A `weekly` unit is the days of
    its week under that same frequency version (a version starting mid-week counts from its
    `valid_from`), and asks the lesser of `times_per_week` and the days left out of pauses.
    """
    found: list[Unit] = []
    day = habit.started_on
    while day <= today:
        frequency = frequency_for(habit.frequencies, day)
        if frequency is None:
            day += timedelta(days=1)
            continue
        if frequency.kind == HabitFrequencyKind.WEEKLY:
            end = week_start(day) + timedelta(days=6)
            days = []
            cursor = day
            while cursor <= end and frequency_for(habit.frequencies, cursor) == frequency:
                days.append(cursor)
                cursor += timedelta(days=1)
            open_days = [d for d in days if not paused(habit.pauses, d)]
            if open_days:
                done = sum(1 for d in open_days if d <= today and day_met(habit, d))
                found.append(
                    Unit(
                        weekly=True,
                        first=days[0],
                        last=days[-1],
                        required=min(frequency.times_per_week or 1, len(open_days)),
                        done=done,
                        closed=days[-1] < today,
                    )
                )
            day = days[-1] + timedelta(days=1)
            continue
        if _scheduled_on(frequency, day) and not paused(habit.pauses, day):
            met = day_met(habit, day)
            found.append(Unit(False, day, day, 1, int(met), closed=day < today))
        day += timedelta(days=1)
    return found


def streaks(found: Sequence[Unit]) -> tuple[int, int]:
    """H4: the current streak and the best one.

    Units met in a row, from the latest back. The open unit (today, the week in progress) does not
    break the streak while unmet, and counts once met. Pauses have no units: they neither break nor
    count.
    """
    best = run = 0
    for unit in found:
        if unit.met:
            run += 1
            best = max(best, run)
        elif unit.closed:
            run = 0
    current = 0
    for unit in reversed(found):
        if unit.met:
            current += 1
        elif unit.closed:
            break
    return current, best


def rate_percent(found: Sequence[Unit], frequency: Frequency | None, today: date) -> int | None:
    """H5: met over scheduled, as a rounded percentage; None with nothing scheduled.

    Days: the last 30, today included once met (an open day neither helps nor hurts). `weekly`:
    the last 4 complete weeks.
    """
    if frequency is not None and frequency.kind == HabitFrequencyKind.WEEKLY:
        current = week_start(today)
        first = current - timedelta(weeks=RATE_WEEKS)
        window = [u for u in found if u.weekly and u.closed and first <= u.first < current]
    else:
        first = today - timedelta(days=RATE_DAYS - 1)
        window = [u for u in found if not u.weekly and u.first >= first and (u.closed or u.met)]
    if not window:
        return None
    return round(100 * sum(1 for u in window if u.met) / len(window))


def current_week(found: Sequence[Unit], today: date) -> Unit | None:
    """H6: the `weekly` unit with today in it."""
    for unit in reversed(found):
        if unit.weekly and unit.first <= today <= unit.last:
            return unit
    return None


def scheduled_today(found: Sequence[Unit], today: date) -> Unit | None:
    """The unit that asks something of today: today's day, or the week in progress."""
    for unit in reversed(found):
        if unit.first <= today <= unit.last:
            return unit
        if unit.last < today:
            return None
    return None


def day_status(habit: Habit, day: date, today: date) -> CalendarStatus:
    """A day of the calendar: done, partial, missed, pending (today), paused or unscheduled."""
    if day > today:
        return CalendarStatus.FUTURE
    if day < habit.started_on:
        return CalendarStatus.UNSCHEDULED
    if paused(habit.pauses, day):
        return CalendarStatus.PAUSED
    if day_met(habit, day):
        return CalendarStatus.DONE
    if habit.entries.get(day, 0) > 0:
        return CalendarStatus.PARTIAL
    frequency = frequency_for(habit.frequencies, day)
    if frequency is None or not _scheduled_on(frequency, day):
        # In `weekly` the unit is the week: a day without an entry is not missed.
        return CalendarStatus.UNSCHEDULED
    return CalendarStatus.PENDING if day == today else CalendarStatus.MISSED


@dataclass(frozen=True)
class Clean:
    """H7: a habit to quit."""

    since: datetime
    days: int
    best_days: int
    relapses_30d: int


def start_moment(started_on: date, tz: ZoneInfo) -> datetime:
    return datetime.combine(started_on, time.min, tzinfo=tz)


def clean(started_on: date, relapses: Iterable[datetime], now: datetime, tz: ZoneInfo) -> Clean:
    """H7: time without since the last relapse (or the start), best stretch, last 30 days."""
    start = start_moment(started_on, tz)
    moments = sorted(r for r in relapses if r >= start)
    since = moments[-1] if moments else start
    points = [start, *moments, now]
    best = max((b - a).days for a, b in pairwise(points))
    recent = sum(1 for r in moments if r >= now - RELAPSE_WINDOW)
    return Clean(
        since=since, days=max(0, (now - since).days), best_days=max(0, best), relapses_30d=recent
    )
