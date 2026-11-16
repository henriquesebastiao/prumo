"""Which days a frequency asks for (H2): the single place that knows the recurrences. Pure, no I/O.

Two ways of scheduling:

- Fixed dates (`daily`, `weekdays`, `month_days`, `month_weekday`): each scheduled day is a unit.
- A flexible window (`per_period`): `times` days in a week, a fortnight or a calendar month; the
  unit is the period.

Every cadence is anchored to the `valid_from` of its version: the week (Monday to Sunday) holding
it for `every_n_weeks` and fortnights, its month for `every_n_months`.
"""

import calendar
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, timedelta
from enum import StrEnum


class HabitFrequencyKind(StrEnum):
    DAILY = "daily"
    # Only accepted on input (apps before D48); stored as `per_period` with `period = week`.
    WEEKLY = "weekly"
    WEEKDAYS = "weekdays"
    MONTH_DAYS = "month_days"
    MONTH_WEEKDAY = "month_weekday"
    PER_PERIOD = "per_period"


class Period(StrEnum):
    WEEK = "week"
    FORTNIGHT = "fortnight"
    MONTH = "month"


class Cadence(StrEnum):
    """How often a frequency comes back, for filters and labels."""

    DAILY = "daily"
    WEEKLY = "weekly"
    FORTNIGHTLY = "fortnightly"
    MONTHLY = "monthly"
    LONGER = "longer"


FIXED_KINDS = frozenset(
    {
        HabitFrequencyKind.DAILY,
        HabitFrequencyKind.WEEKDAYS,
        HabitFrequencyKind.MONTH_DAYS,
        HabitFrequencyKind.MONTH_WEEKDAY,
    }
)
LAST = -1
"""`week_of_month` of the last weekday of the month."""

PERIOD_DAYS = {Period.WEEK: 7, Period.FORTNIGHT: 14, Period.MONTH: 28}
"""The most `times` a period takes: its days (the shortest month for `month`)."""


@dataclass(frozen=True)
class Frequency:
    valid_from: date
    kind: HabitFrequencyKind
    times: int | None = None
    weekdays: tuple[int, ...] = ()
    every_n: int = 1
    month_days: tuple[int, ...] = ()
    month_last_day: bool = False
    week_of_month: int | None = None
    weekday: int | None = None
    period: Period | None = None
    preferred_day: int | None = None

    @property
    def periodic(self) -> bool:
        return self.kind == HabitFrequencyKind.PER_PERIOD


def week_start(day: date) -> date:
    return day - timedelta(days=day.weekday())


def last_day(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]


def month_end(day: date) -> date:
    return day.replace(day=last_day(day.year, day.month))


def _months_between(first: date, day: date) -> int:
    return (day.year - first.year) * 12 + day.month - first.month


def nth_weekday(year: int, month: int, week_of_month: int, weekday: int) -> date:
    """The 1st to 4th `weekday` of the month, or the last one (`LAST`)."""
    if week_of_month == LAST:
        end = date(year, month, last_day(year, month))
        return end - timedelta(days=(end.weekday() - weekday) % 7)
    first = date(year, month, 1)
    return first + timedelta(days=(weekday - first.weekday()) % 7 + 7 * (week_of_month - 1))


def month_days_of(frequency: Frequency, year: int, month: int) -> set[int]:
    """The days of a month: a day it lacks falls on its last day, without repeating."""
    end = last_day(year, month)
    found = {min(day, end) for day in frequency.month_days}
    if frequency.month_last_day:
        found.add(end)
    return found


def occurs_on(frequency: Frequency, day: date) -> bool:
    """Fixed dates: whether `day` is one of them. Always false in `per_period`."""
    kind = frequency.kind
    if kind == HabitFrequencyKind.DAILY:
        return True
    if kind == HabitFrequencyKind.WEEKDAYS:
        if day.weekday() not in frequency.weekdays:
            return False
        weeks = (week_start(day) - week_start(frequency.valid_from)).days // 7
        return weeks % frequency.every_n == 0
    if kind in (HabitFrequencyKind.MONTH_DAYS, HabitFrequencyKind.MONTH_WEEKDAY):
        if _months_between(frequency.valid_from, day) % frequency.every_n != 0:
            return False
        if kind == HabitFrequencyKind.MONTH_DAYS:
            return day.day in month_days_of(frequency, day.year, day.month)
        if frequency.week_of_month is None or frequency.weekday is None:
            return False
        return day == nth_weekday(day.year, day.month, frequency.week_of_month, frequency.weekday)
    return False


def period_bounds(frequency: Frequency, day: date) -> tuple[date, date]:
    """`per_period`: the first and last day of the period holding `day`, whole (not cut by
    versions). Weeks run Monday to Sunday; fortnights are 14-day blocks from the Monday of the
    week of `valid_from`; months are calendar months."""
    if frequency.period == Period.MONTH:
        return day.replace(day=1), month_end(day)
    if frequency.period == Period.FORTNIGHT:
        anchor = week_start(frequency.valid_from)
        start = anchor + timedelta(days=14 * ((day - anchor).days // 14))
        return start, start + timedelta(days=13)
    start = week_start(day)
    return start, start + timedelta(days=6)


def preferred_date(frequency: Frequency, start: date, end: date) -> date | None:
    """`per_period`: the preferred day inside the period `start`..`end`, if any. A weekday in weeks
    and fortnights (its first one in the fortnight); a day of the month, limited to its end."""
    preferred = frequency.preferred_day
    if preferred is None:
        return None
    if frequency.period == Period.MONTH:
        return start.replace(day=min(preferred, last_day(start.year, start.month)))
    found = start + timedelta(days=(preferred - start.weekday()) % 7)
    return found if found <= end else None


def cadence(frequency: Frequency) -> Cadence:
    kind = frequency.kind
    if kind == HabitFrequencyKind.DAILY:
        return Cadence.DAILY
    if kind == HabitFrequencyKind.WEEKDAYS:
        return {1: Cadence.WEEKLY, 2: Cadence.FORTNIGHTLY}.get(frequency.every_n, Cadence.LONGER)
    if kind == HabitFrequencyKind.PER_PERIOD:
        return {
            Period.WEEK: Cadence.WEEKLY,
            Period.FORTNIGHT: Cadence.FORTNIGHTLY,
            Period.MONTH: Cadence.MONTHLY,
        }[frequency.period or Period.WEEK]
    return Cadence.MONTHLY if frequency.every_n == 1 else Cadence.LONGER


def frequency_for(frequencies: Iterable[Frequency], day: date) -> Frequency | None:
    """H2: the version in force on `day` (the latest `valid_from` <= day)."""
    chosen: Frequency | None = None
    for frequency in frequencies:
        if frequency.valid_from <= day and (
            chosen is None or frequency.valid_from > chosen.valid_from
        ):
            chosen = frequency
    return chosen
