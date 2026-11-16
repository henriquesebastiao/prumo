"""The recurrence engine (H2) in tables: which days each frequency asks for."""

from datetime import date, timedelta

import pytest

from prumo.modules.habits.recurrence import (
    LAST,
    Cadence,
    Frequency,
    HabitFrequencyKind,
    Period,
    cadence,
    month_days_of,
    nth_weekday,
    occurs_on,
    period_bounds,
    preferred_date,
)

K = HabitFrequencyKind


def month_days(
    *days: int, last: bool = False, every: int = 1, start: date | None = None
) -> Frequency:
    return Frequency(
        start or date(2026, 1, 1), K.MONTH_DAYS, month_days=days, month_last_day=last, every_n=every
    )


def dates_in(frequency: Frequency, first: date, last: date) -> list[date]:
    days = (last - first).days + 1
    return [d for d in (first + timedelta(days=i) for i in range(days)) if occurs_on(frequency, d)]


@pytest.mark.parametrize(
    ("year", "month", "expected"),
    [
        (2026, 1, 31),  # 31 days
        (2026, 4, 30),  # 30 days: the 31st falls on the 30th
        (2026, 2, 28),  # 28 days
        (2028, 2, 29),  # 29 days (leap year)
    ],
)
def test_the_31st_falls_on_the_last_day_of_shorter_months(
    year: int, month: int, expected: int
) -> None:
    frequency = month_days(31)
    assert month_days_of(frequency, year, month) == {expected}
    assert dates_in(frequency, date(year, month, 1), date(year, month, expected)) == [
        date(year, month, expected)
    ]


@pytest.mark.parametrize(
    ("days", "last", "year", "month", "expected"),
    [
        ((29, 30, 31), False, 2026, 2, {28}),  # no repetition
        ((29, 30, 31), False, 2028, 2, {29}),
        ((1, 15), True, 2026, 4, {1, 15, 30}),
        ((), True, 2026, 2, {28}),
        ((30,), True, 2026, 4, {30}),  # the 30th is the last day: once
    ],
)
def test_month_days_and_the_last_day_without_repeating(
    days: tuple[int, ...], last: bool, year: int, month: int, expected: set[int]
) -> None:
    assert month_days_of(month_days(*days, last=last), year, month) == expected


def test_every_three_months_from_the_month_of_valid_from() -> None:
    tank = month_days(5, every=3, start=date(2026, 8, 1))
    assert dates_in(tank, date(2026, 8, 1), date(2027, 3, 31)) == [
        date(2026, 8, 5),
        date(2026, 11, 5),
        date(2027, 2, 5),
    ]


@pytest.mark.parametrize(
    ("year", "month", "week", "weekday", "expected"),
    [
        (2026, 11, 1, 6, date(2026, 11, 1)),  # first Sunday on the 1st
        (2026, 12, 1, 6, date(2026, 12, 6)),
        (2026, 11, LAST, 5, date(2026, 11, 28)),  # last Saturday
        (2026, 2, LAST, 5, date(2026, 2, 28)),  # last Saturday on the last day
        (2026, 2, 4, 5, date(2026, 2, 28)),
        (2026, 5, LAST, 6, date(2026, 5, 31)),
        (2026, 11, 2, 1, date(2026, 11, 10)),  # second Tuesday
    ],
)
def test_the_nth_weekday_of_the_month(
    year: int, month: int, week: int, weekday: int, expected: date
) -> None:
    assert nth_weekday(year, month, week, weekday) == expected


def test_last_saturday_every_other_month() -> None:
    frequency = Frequency(
        date(2026, 11, 1), K.MONTH_WEEKDAY, week_of_month=LAST, weekday=5, every_n=2
    )
    assert dates_in(frequency, date(2026, 11, 1), date(2027, 3, 31)) == [
        date(2026, 11, 28),
        date(2027, 1, 30),
        date(2027, 3, 27),
    ]


def test_every_other_saturday_anchored_on_the_week_of_valid_from_across_the_year() -> None:
    sheets = Frequency(date(2026, 12, 26), K.WEEKDAYS, weekdays=(5,), every_n=2)
    assert dates_in(sheets, date(2026, 12, 20), date(2027, 1, 31)) == [
        date(2026, 12, 26),
        date(2027, 1, 9),
        date(2027, 1, 23),
    ]
    # A version from mid-week keeps the anchor in its Monday: Saturday of that same week counts.
    midweek = Frequency(date(2026, 12, 23), K.WEEKDAYS, weekdays=(5,), every_n=2)
    assert dates_in(midweek, date(2026, 12, 23), date(2027, 1, 10)) == [
        date(2026, 12, 26),
        date(2027, 1, 9),
    ]


@pytest.mark.parametrize(
    ("period", "day", "expected"),
    [
        (Period.WEEK, date(2026, 11, 17), (date(2026, 11, 16), date(2026, 11, 22))),
        (Period.MONTH, date(2027, 2, 10), (date(2027, 2, 1), date(2027, 2, 28))),
        (Period.MONTH, date(2028, 2, 10), (date(2028, 2, 1), date(2028, 2, 29))),
        # Fortnights from the Monday of the week of valid_from (21/12/2026), across the year.
        (Period.FORTNIGHT, date(2026, 12, 26), (date(2026, 12, 21), date(2027, 1, 3))),
        (Period.FORTNIGHT, date(2027, 1, 3), (date(2026, 12, 21), date(2027, 1, 3))),
        (Period.FORTNIGHT, date(2027, 1, 4), (date(2027, 1, 4), date(2027, 1, 17))),
    ],
)
def test_period_bounds(period: Period, day: date, expected: tuple[date, date]) -> None:
    frequency = Frequency(date(2026, 12, 26), K.PER_PERIOD, times=1, period=period)
    assert period_bounds(frequency, day) == expected
    assert not occurs_on(frequency, day)


@pytest.mark.parametrize(
    ("period", "preferred", "start", "end", "expected"),
    [
        (Period.MONTH, 31, date(2026, 2, 1), date(2026, 2, 28), date(2026, 2, 28)),
        (Period.MONTH, 15, date(2026, 11, 1), date(2026, 11, 30), date(2026, 11, 15)),
        (Period.WEEK, 5, date(2026, 11, 16), date(2026, 11, 22), date(2026, 11, 21)),
        (Period.FORTNIGHT, 5, date(2026, 12, 21), date(2027, 1, 3), date(2026, 12, 26)),
        (Period.WEEK, None, date(2026, 11, 16), date(2026, 11, 22), None),
    ],
)
def test_the_preferred_day_of_a_period(
    period: Period, preferred: int | None, start: date, end: date, expected: date | None
) -> None:
    frequency = Frequency(start, K.PER_PERIOD, times=1, period=period, preferred_day=preferred)
    assert preferred_date(frequency, start, end) == expected


@pytest.mark.parametrize(
    ("frequency", "expected"),
    [
        (Frequency(date(2026, 1, 1), K.DAILY), Cadence.DAILY),
        (Frequency(date(2026, 1, 1), K.WEEKDAYS, weekdays=(0,)), Cadence.WEEKLY),
        (Frequency(date(2026, 1, 1), K.WEEKDAYS, weekdays=(5,), every_n=2), Cadence.FORTNIGHTLY),
        (Frequency(date(2026, 1, 1), K.WEEKDAYS, weekdays=(5,), every_n=4), Cadence.LONGER),
        (month_days(5), Cadence.MONTHLY),
        (month_days(5, every=3), Cadence.LONGER),
        (
            Frequency(date(2026, 1, 1), K.MONTH_WEEKDAY, week_of_month=1, weekday=6),
            Cadence.MONTHLY,
        ),
        (Frequency(date(2026, 1, 1), K.PER_PERIOD, times=2, period=Period.WEEK), Cadence.WEEKLY),
        (
            Frequency(date(2026, 1, 1), K.PER_PERIOD, times=1, period=Period.FORTNIGHT),
            Cadence.FORTNIGHTLY,
        ),
        (Frequency(date(2026, 1, 1), K.PER_PERIOD, times=2, period=Period.MONTH), Cadence.MONTHLY),
    ],
)
def test_cadence(frequency: Frequency, expected: Cadence) -> None:
    assert cadence(frequency) == expected
