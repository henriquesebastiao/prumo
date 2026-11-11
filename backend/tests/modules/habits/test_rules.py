from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from prumo.modules.habits import rules
from prumo.modules.habits.rules import CalendarStatus, Frequency, Habit, HabitFrequencyKind, Pause

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
    assert rules.scheduled_today(rules.units(habit(entries, pauses=(still,)), TODAY), TODAY) is None


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


def test_a_weekly_habit_counts_weeks_and_the_week_in_progress() -> None:
    weekly = Frequency(date(2026, 10, 5), HabitFrequencyKind.WEEKLY, times_per_week=3)
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
    assert all(u.weekly for u in found)
    week = rules.current_week(found, TODAY)
    assert week is not None
    assert (week.done, week.required, week.closed) == (1, 3, False)
    # The week in progress does not break the streak; the missed week does.
    assert rules.streaks(found) == (3, 3)
    # The last 4 complete weeks: 19/10 (missed), 26/10, 2/11, 9/11.
    assert rules.rate_percent(found, weekly, TODAY) == 75
    assert rules.day_status(gym, date(2026, 11, 10), TODAY) == CalendarStatus.UNSCHEDULED


def test_a_weekly_frequency_starting_mid_week_asks_only_the_days_left() -> None:
    weekly = Frequency(date(2026, 11, 14), HabitFrequencyKind.WEEKLY, times_per_week=3)
    late = habit({date(2026, 11, 14): 1}, started_on=date(2026, 11, 14), frequencies=(weekly,))
    first = rules.units(late, TODAY)[0]
    assert (first.first, first.last, first.required, first.met) == (
        date(2026, 11, 14),
        date(2026, 11, 15),
        2,
        False,
    )


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
