from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from prumo.modules.habits import rules
from prumo.modules.habits.rules import (
    CalendarStatus,
    Frequency,
    Habit,
    HabitFrequencyKind,
    Pause,
    Period,
)

SP = ZoneInfo("America/Sao_Paulo")
TODAY = date(2026, 11, 17)  # Tuesday
DAILY = Frequency(date(2026, 11, 1), HabitFrequencyKind.DAILY)


def days(first: date, last: date) -> list[date]:
    return [first + timedelta(days=i) for i in range((last - first).days + 1)]


def habit(
    entries: dict[date, int] | None = None,
    *,
    started_on: date = date(2026, 11, 1),
    frequencies: tuple[Frequency, ...] = (DAILY,),
    pauses: tuple[Pause, ...] = (),
    measure: str = "check",
    target: int | None = None,
) -> Habit:
    return Habit(started_on, measure, target, frequencies, pauses, entries or {})


def test_a_day_is_met_by_an_entry_or_by_reaching_the_target() -> None:
    check = habit({TODAY: 1})
    assert rules.day_met(check, TODAY)
    water = habit({TODAY: 1250, date(2026, 11, 16): 2000}, measure="quantity", target=2000)
    assert not rules.day_met(water, TODAY)
    assert rules.day_met(water, date(2026, 11, 16))
    assert rules.day_status(water, TODAY, TODAY) == CalendarStatus.PARTIAL


def test_the_streak_does_not_break_on_an_open_today_and_counts_it_once_met() -> None:
    entries = dict.fromkeys(days(date(2026, 11, 10), date(2026, 11, 16)), 1)
    current, best = rules.streaks(rules.units(habit(entries), TODAY))
    assert (current, best) == (7, 7)
    current, best = rules.streaks(rules.units(habit(entries | {TODAY: 1}), TODAY))
    assert (current, best) == (8, 8)
    # A missed day breaks it: the 9th is missing.
    current, best = rules.streaks(rules.units(habit({**entries, date(2026, 11, 8): 1}), TODAY))
    assert (current, best) == (7, 7)


def test_a_pause_neither_breaks_nor_counts() -> None:
    entries = {d: 1 for d in days(date(2026, 11, 1), date(2026, 11, 16)) if not 5 <= d.day <= 9}
    pause = Pause(date(2026, 11, 5), date(2026, 11, 9))
    found = rules.units(habit(entries, pauses=(pause,)), TODAY)
    assert date(2026, 11, 7) not in {u.first for u in found}
    assert rules.streaks(found) == (11, 11)
    assert (
        rules.day_status(habit(entries, pauses=(pause,)), date(2026, 11, 7), TODAY)
        == CalendarStatus.PAUSED
    )
    # An open pause has no end.
    still = Pause(date(2026, 11, 15), None)
    assert rules.unit_on(rules.units(habit(entries, pauses=(still,)), TODAY), TODAY) is None


def test_weekdays_and_a_frequency_that_changed() -> None:
    weekdays = Frequency(date(2026, 11, 9), HabitFrequencyKind.WEEKDAYS, weekdays=(0, 1, 2, 3, 4))
    anki = habit(frequencies=(DAILY, weekdays))
    found = rules.units(anki, TODAY)
    # Daily from 1 to 8 (8 days), then Monday to Friday: 9 to 13 and 16, 17.
    assert len(found) == 8 + 5 + 2
    assert rules.day_status(anki, date(2026, 11, 14), TODAY) == CalendarStatus.UNSCHEDULED
    assert rules.day_status(anki, date(2026, 11, 13), TODAY) == CalendarStatus.MISSED
    assert rules.day_status(anki, TODAY, TODAY) == CalendarStatus.PENDING
    assert rules.day_status(anki, date(2026, 11, 18), TODAY) == CalendarStatus.FUTURE
    assert rules.day_status(anki, date(2026, 10, 31), TODAY) == CalendarStatus.UNSCHEDULED


def per_week(valid_from: date, times: int) -> Frequency:
    return Frequency(valid_from, HabitFrequencyKind.PER_PERIOD, times=times, period=Period.WEEK)


def test_a_weekly_habit_counts_weeks_and_the_week_in_progress() -> None:
    weekly = per_week(date(2026, 10, 5), 3)
    entries = {
        # three full weeks met, one missed (19-25/10 with 2), this week 1 of 3
        **dict.fromkeys((date(2026, 10, 5), date(2026, 10, 7), date(2026, 10, 9)), 1),
        **dict.fromkeys((date(2026, 10, 12), date(2026, 10, 14), date(2026, 10, 16)), 1),
        **dict.fromkeys((date(2026, 10, 20), date(2026, 10, 22)), 1),
        **dict.fromkeys((date(2026, 10, 26), date(2026, 10, 28), date(2026, 10, 30)), 1),
        **dict.fromkeys((date(2026, 11, 2), date(2026, 11, 4), date(2026, 11, 6)), 1),
        **dict.fromkeys((date(2026, 11, 9), date(2026, 11, 11), date(2026, 11, 13)), 1),
        date(2026, 11, 16): 1,
    }
    gym = habit(entries, started_on=date(2026, 10, 5), frequencies=(weekly,))
    found = rules.units(gym, TODAY)
    assert all(u.periodic for u in found)
    week = rules.current_period(found, TODAY)
    assert week is not None
    assert (week.done, week.required, week.closed) == (1, 3, False)
    # The week in progress does not break the streak; the missed week does.
    assert rules.streaks(found) == (3, 3)
    # The last 4 complete weeks: 19/10 (missed), 26/10, 2/11, 9/11.
    assert rules.rate_percent(found, weekly, TODAY) == 75
    assert rules.day_status(gym, date(2026, 11, 10), TODAY) == CalendarStatus.UNSCHEDULED


def test_a_period_cut_by_the_start_is_neutral_and_asks_only_the_days_left() -> None:
    weekly = per_week(date(2026, 11, 14), 3)
    late = habit({date(2026, 11, 14): 1}, started_on=date(2026, 11, 14), frequencies=(weekly,))
    first = rules.units(late, TODAY)[0]
    assert (first.first, first.last, first.required, first.met, first.neutral) == (
        date(2026, 11, 14),
        date(2026, 11, 15),
        2,
        False,
        True,
    )
    # H2a: unmet and neutral, it neither breaks the streak nor enters the rate.
    assert rules.rate_percent(rules.units(late, TODAY), weekly, TODAY) is None


def test_the_rate_uses_30_days_and_today_only_once_met() -> None:
    started = date(2026, 10, 1)
    frequencies = (Frequency(started, HabitFrequencyKind.DAILY),)
    entries = {d: 1 for d in days(date(2026, 10, 19), date(2026, 11, 16)) if d.day % 2 == 0}
    reading = habit(entries, started_on=started, frequencies=frequencies)
    # 19/10 to 16/11: 29 closed days, the even ones met (14); today is open and left out.
    assert rules.rate_percent(rules.units(reading, TODAY), DAILY, TODAY) == 48
    # Once today is met, it counts: 15 of 30.
    done = habit(entries | {TODAY: 1}, started_on=started, frequencies=frequencies)
    assert rules.rate_percent(rules.units(done, TODAY), DAILY, TODAY) == 50
    assert rules.rate_percent(rules.units(habit(started_on=TODAY), TODAY), DAILY, TODAY) is None


def test_days_before_the_start_and_future_days_do_not_count() -> None:
    fresh = habit(started_on=TODAY)
    assert [u.first for u in rules.units(fresh, TODAY)] == [TODAY]
    assert rules.streaks(rules.units(fresh, TODAY)) == (0, 0)


def test_time_without_a_bad_habit() -> None:
    now = datetime(2026, 11, 17, 14, 30, tzinfo=SP)
    relapses = [
        datetime(2026, 9, 12, 23, 0, tzinfo=SP),
        datetime(2026, 10, 3, 22, 0, tzinfo=SP),
        datetime(2026, 11, 8, 23, 30, tzinfo=SP),
    ]
    clean = rules.clean(date(2026, 8, 1), relapses, now, SP)
    assert clean.since == relapses[-1]
    assert clean.days == 8
    # 1/8 to 12/9 is the longest stretch: 42 days and 23 hours.
    assert clean.best_days == 42
    assert clean.relapses_30d == 1
    fresh = rules.clean(date(2026, 11, 10), [], now, SP)
    assert fresh.since == datetime(2026, 11, 10, tzinfo=SP)
    assert fresh.days == 7


GYM = per_week(date(2026, 10, 5), 3)


def three(monday: date) -> dict[date, int]:
    return dict.fromkeys((monday, monday + timedelta(days=2), monday + timedelta(days=4)), 1)


def test_a_pause_over_half_a_period_makes_it_neutral() -> None:
    # 2/11 to 5/11: 4 of the 7 days paused; the week asks min(3, 3 open days) and is neutral.
    half = Pause(date(2026, 11, 2), date(2026, 11, 5))
    entries = three(date(2026, 10, 26)) | three(date(2026, 11, 9))
    gym = habit(entries, started_on=date(2026, 10, 5), frequencies=(GYM,), pauses=(half,))
    week = next(u for u in rules.units(gym, TODAY) if u.first == date(2026, 11, 2))
    assert (week.required, week.done, week.neutral) == (3, 0, True)
    # The neutral week neither breaks the streak (26/10 and 9/11 in a row) nor enters the rate.
    assert rules.streaks(rules.units(gym, TODAY))[0] == 2
    # 3 of 7 days paused: the week counts, asking min(3, 4).
    short = Pause(date(2026, 11, 2), date(2026, 11, 4))
    gym = habit(entries, started_on=date(2026, 10, 5), frequencies=(GYM,), pauses=(short,))
    week = next(u for u in rules.units(gym, TODAY) if u.first == date(2026, 11, 2))
    assert (week.required, week.neutral, week.closed) == (3, False, True)
    assert rules.streaks(rules.units(gym, TODAY))[0] == 1
    # A pause over the whole week leaves no unit at all.
    whole = Pause(date(2026, 11, 2), date(2026, 11, 8))
    gym = habit(entries, started_on=date(2026, 10, 5), frequencies=(GYM,), pauses=(whole,))
    assert date(2026, 11, 2) not in {u.first for u in rules.units(gym, TODAY)}


def test_a_version_change_mid_period_leaves_both_sides_neutral() -> None:
    fortnight = Frequency(
        date(2026, 11, 11), HabitFrequencyKind.PER_PERIOD, times=2, period=Period.FORTNIGHT
    )
    entries = three(date(2026, 11, 2)) | {date(2026, 11, 12): 1}
    gym = habit(entries, started_on=date(2026, 10, 26), frequencies=(GYM, fortnight))
    found = rules.units(gym, TODAY)
    cut_week, cut_fortnight = found[-2], found[-1]
    # The week of 9/11 under the old version is 9 and 10 only; the fortnight from 9/11 (anchored on
    # the Monday of the week of 11/11) starts on 11/11 under the new one.
    assert (cut_week.first, cut_week.last, cut_week.neutral, cut_week.met) == (
        date(2026, 11, 9),
        date(2026, 11, 10),
        True,
        False,
    )
    assert (cut_fortnight.start, cut_fortnight.end) == (date(2026, 11, 9), date(2026, 11, 22))
    assert (cut_fortnight.first, cut_fortnight.neutral, cut_fortnight.done) == (
        date(2026, 11, 11),
        True,
        1,
    )
    # 26/10 missed, 2/11 met; the neutral week doesn't break it.
    assert rules.streaks(found) == (1, 1)
    # A neutral period met still counts.
    met = habit(entries | {TODAY: 1}, started_on=date(2026, 10, 26), frequencies=(GYM, fortnight))
    assert rules.streaks(rules.units(met, TODAY)) == (2, 2)


def test_sparse_cadences_rate_the_last_six_occurrences() -> None:
    fortnightly = Frequency(date(2026, 7, 4), HabitFrequencyKind.WEEKDAYS, weekdays=(5,), every_n=2)
    saturdays = [date(2026, 7, 4) + timedelta(weeks=2 * i) for i in range(10)]
    assert saturdays[-1] == date(2026, 11, 7)
    # Met the first 6, missed the last 4: the window is the last 6, 2 of them met.
    entries = dict.fromkeys(saturdays[:6], 1)
    sheets = habit(entries, started_on=date(2026, 7, 4), frequencies=(fortnightly,))
    found = rules.units(sheets, TODAY)
    assert [u.first for u in found] == saturdays
    assert rules.rate_percent(found, fortnightly, TODAY) == 33
    assert rules.streak_unit(fortnightly) == "occurrence"
    assert rules.next_due(sheets, found, TODAY) == date(2026, 11, 21)


def test_monthly_periods_and_the_next_due_day() -> None:
    monthly = Frequency(
        date(2026, 9, 1),
        HabitFrequencyKind.PER_PERIOD,
        times=1,
        period=Period.MONTH,
        preferred_day=15,
    )
    chore = habit({date(2026, 9, 6): 1}, started_on=date(2026, 9, 1), frequencies=(monthly,))
    found = rules.units(chore, TODAY)
    assert [(u.first, u.last, u.met) for u in found] == [
        (date(2026, 9, 1), date(2026, 9, 30), True),
        (date(2026, 10, 1), date(2026, 10, 31), False),
        (date(2026, 11, 1), date(2026, 11, 30), False),
    ]
    # Open, with the preferred day already past: due today.
    assert rules.next_due(chore, found, TODAY) == TODAY
    assert rules.streak_unit(monthly) == "month"
    assert rules.rate_percent(found, monthly, TODAY) == 50
    # Met this month: the preferred day of the next one.
    done = habit({date(2026, 11, 3): 1}, started_on=date(2026, 9, 1), frequencies=(monthly,))
    assert rules.next_due(done, rules.units(done, TODAY), TODAY) == date(2026, 12, 15)
    # A preferred day still ahead in the open month.
    later = Frequency(
        date(2026, 9, 1),
        HabitFrequencyKind.PER_PERIOD,
        times=1,
        period=Period.MONTH,
        preferred_day=20,
    )
    ahead = habit(started_on=date(2026, 9, 1), frequencies=(later,))
    assert rules.next_due(ahead, rules.units(ahead, TODAY), TODAY) == date(2026, 11, 20)
    # Under an open pause nothing is due.
    stopped = habit(started_on=date(2026, 9, 1), frequencies=(later,), pauses=(Pause(TODAY, None),))
    assert rules.next_due(stopped, rules.units(stopped, TODAY), TODAY) is None


def test_the_next_due_day_of_fixed_dates() -> None:
    daily = habit()
    assert rules.next_due(daily, rules.units(daily, TODAY), TODAY) == TODAY
    met = habit({TODAY: 1})
    assert rules.next_due(met, rules.units(met, TODAY), TODAY) == date(2026, 11, 18)
    review = Frequency(
        date(2026, 11, 1), HabitFrequencyKind.MONTH_WEEKDAY, week_of_month=1, weekday=6
    )
    first_sunday = habit(frequencies=(review,))
    found = rules.units(first_sunday, TODAY)
    assert [u.first for u in found] == [date(2026, 11, 1)]
    assert rules.next_due(first_sunday, found, TODAY) == date(2026, 12, 6)
    # A pause skips the days under it.
    paused = habit(frequencies=(review,), pauses=(Pause(date(2026, 12, 1), date(2026, 12, 31)),))
    assert rules.next_due(paused, rules.units(paused, TODAY), TODAY) == date(2027, 1, 3)
