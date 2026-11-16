"""Pure calculations of the habits rules (no database). See docs/dominio.md, H1-H7.

Which days a frequency asks for lives in `recurrence`; this module turns them into units (H2),
streaks (H4), rates (H5), the period in progress (H6) and the next due day.
"""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from enum import StrEnum
from itertools import pairwise
from typing import Literal
from zoneinfo import ZoneInfo

from prumo.modules.habits.recurrence import (
    Cadence,
    Frequency,
    HabitFrequencyKind,
    Period,
    frequency_for,
    occurs_on,
    period_bounds,
    preferred_date,
    week_start,
)

__all__ = [
    "Cadence",
    "CalendarStatus",
    "Frequency",
    "Habit",
    "HabitFrequencyKind",
    "Pause",
    "Period",
    "Unit",
    "frequency_for",
    "week_start",
]

RATE_DAYS = 30
RATE_WEEKS = 4
RATE_UNITS = 6
RELAPSE_WINDOW = timedelta(days=30)
NEXT_DUE_HORIZON = timedelta(days=3 * 366)

StreakUnit = Literal["day", "occurrence", "week", "fortnight", "month"]


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
    """A scheduled unit (H2): a day of fixed dates, or a period in `per_period`.

    A `neutral` period (H2a) neither enters the rate nor breaks the streak, but counts in the
    streak once met: a pause covers half of it or more, or a version change cuts it.
    """

    periodic: bool
    first: date
    last: date
    required: int
    done: int
    closed: bool
    neutral: bool = False
    period: Period | None = None
    start: date | None = None
    end: date | None = None

    @property
    def met(self) -> bool:
        return self.done >= self.required


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


def _period_unit(
    habit: Habit, frequency: Frequency, day: date, today: date
) -> tuple[Unit | None, date]:
    """The `per_period` unit from `day` on, and the day after it."""
    start, end = period_bounds(frequency, day)
    days = []
    cursor = day
    while cursor <= end and frequency_for(habit.frequencies, cursor) == frequency:
        days.append(cursor)
        cursor += timedelta(days=1)
    following = days[-1] + timedelta(days=1)
    open_days = [d for d in days if not paused(habit.pauses, d)]
    if not open_days:
        return None, following
    paused_days = len(days) - len(open_days)
    cut = days[0] != start or days[-1] != end
    unit = Unit(
        periodic=True,
        first=days[0],
        last=days[-1],
        required=min(frequency.times or 1, len(open_days)),
        done=sum(1 for d in open_days if d <= today and day_met(habit, d)),
        closed=days[-1] < today,
        neutral=cut or 2 * paused_days >= len(days),
        period=frequency.period,
        start=start,
        end=end,
    )
    return unit, following


def units(habit: Habit, today: date) -> list[Unit]:
    """H2: the scheduled units from the start to today, oldest first (a period in progress whole).

    Days in a pause, before the start or in the future don't count. A `per_period` unit is the days
    of its period under that same frequency version and asks the lesser of `times` and the days
    left out of pauses; it is neutral when cut by a version or half paused (H2a).
    """
    found: list[Unit] = []
    day = habit.started_on
    while day <= today:
        frequency = frequency_for(habit.frequencies, day)
        if frequency is None:
            day += timedelta(days=1)
            continue
        if frequency.periodic:
            unit, day = _period_unit(habit, frequency, day, today)
            if unit is not None:
                found.append(unit)
            continue
        if occurs_on(frequency, day) and not paused(habit.pauses, day):
            met = day_met(habit, day)
            found.append(Unit(False, day, day, 1, int(met), closed=day < today))
        day += timedelta(days=1)
    return found


def streaks(found: Sequence[Unit]) -> tuple[int, int]:
    """H4: the current streak and the best one.

    Units met in a row, from the latest back. The open unit (today, the period in progress) and a
    neutral period don't break the streak while unmet, and count once met. Pauses have no units:
    they neither break nor count.
    """
    best = run = 0
    for unit in found:
        if unit.met:
            run += 1
            best = max(best, run)
        elif unit.closed and not unit.neutral:
            run = 0
    current = 0
    for unit in reversed(found):
        if unit.met:
            current += 1
        elif unit.closed and not unit.neutral:
            break
    return current, best


def _rate_window(found: Sequence[Unit], frequency: Frequency, today: date) -> list[Unit]:
    if frequency.periodic:
        periods = [u for u in found if u.periodic and u.closed and not u.neutral]
        if frequency.period == Period.WEEK:
            current = week_start(today)
            first = current - timedelta(weeks=RATE_WEEKS)
            return [u for u in periods if first <= u.first < current]
        return periods[-RATE_UNITS:]
    days = [u for u in found if not u.periodic and (u.closed or u.met)]
    daily = frequency.kind == HabitFrequencyKind.DAILY or (
        frequency.kind == HabitFrequencyKind.WEEKDAYS and frequency.every_n == 1
    )
    if daily:
        first = today - timedelta(days=RATE_DAYS - 1)
        return [u for u in days if u.first >= first]
    return days[-RATE_UNITS:]


def rate_percent(found: Sequence[Unit], frequency: Frequency | None, today: date) -> int | None:
    """H5: met over scheduled, as a rounded percentage; None with nothing scheduled.

    The window follows the cadence of the version in force: daily and weekly fixed dates, the last
    30 days (today included once met); weekly periods, the last 4 complete weeks; anything sparser,
    the last 6 closed occurrences or complete periods. Neutral periods stay out.
    """
    if frequency is None:
        return None
    window = _rate_window(found, frequency, today)
    if not window:
        return None
    return round(100 * sum(1 for u in window if u.met) / len(window))


def unit_on(found: Sequence[Unit], day: date) -> Unit | None:
    """The unit that asks something of `day`: the day itself, or the period holding it."""
    for unit in reversed(found):
        if unit.first <= day <= unit.last:
            return unit
        if unit.last < day:
            return None
    return None


def current_period(found: Sequence[Unit], today: date) -> Unit | None:
    """H6: the `per_period` unit with today in it."""
    unit = unit_on(found, today)
    return unit if unit is not None and unit.periodic else None


def streak_unit(frequency: Frequency | None) -> StreakUnit:
    if frequency is None or frequency.kind == HabitFrequencyKind.DAILY:
        return "day"
    if frequency.periodic:
        return frequency.period.value if frequency.period else "week"
    if frequency.kind == HabitFrequencyKind.WEEKDAYS and frequency.every_n == 1:
        return "day"
    return "occurrence"


def unit_preferred(habit: Habit, unit: Unit) -> date | None:
    """The preferred day of a `per_period` unit, if its version has one."""
    frequency = frequency_for(habit.frequencies, unit.first)
    if frequency is None or unit.start is None or unit.end is None:
        return None
    return preferred_date(frequency, unit.start, unit.end)


def next_due(habit: Habit, found: Sequence[Unit], today: date) -> date | None:
    """The next day that asks something: today while open; in `per_period`, the preferred day of
    the open period (or today once it passed), else the next period. None under an open pause."""
    # Today in a pause asks nothing: look for the first day after it.
    current = None if paused(habit.pauses, today) else unit_on(found, today)
    if current is not None and not current.met:
        if not current.periodic:
            return today
        preferred = unit_preferred(habit, current)
        if (
            preferred is not None
            and today <= preferred <= current.last
            and not paused(habit.pauses, preferred)
        ):
            return preferred
        return today
    day = current.last + timedelta(days=1) if current is not None else today
    day = max(day, habit.started_on)
    horizon = today + NEXT_DUE_HORIZON
    while day <= horizon:
        frequency = frequency_for(habit.frequencies, day)
        if frequency is None or paused(habit.pauses, day):
            day += timedelta(days=1)
            continue
        if frequency.periodic:
            start, end = period_bounds(frequency, day)
            preferred = preferred_date(frequency, start, end)
            if (
                preferred is not None
                and preferred >= day
                and frequency_for(habit.frequencies, preferred) == frequency
                and not paused(habit.pauses, preferred)
            ):
                return preferred
            return day
        if occurs_on(frequency, day):
            return day
        day += timedelta(days=1)
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
    if frequency is None or not occurs_on(frequency, day):
        # In `per_period` the unit is the period: a day without an entry is not missed.
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
