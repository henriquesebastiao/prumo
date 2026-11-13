"""Habits rules (H1-H7): scheduled units, streaks, rates, calendar and clean time."""

from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from pytest_codspeed import BenchmarkFixture

from prumo.modules.habits import rules
from prumo.modules.habits.rules import Frequency, Habit, HabitFrequencyKind, Pause

SP = ZoneInfo("America/Sao_Paulo")
TODAY = date(2026, 11, 17)
STARTED_ON = TODAY - timedelta(days=365)
DAYS = [STARTED_ON + timedelta(days=i) for i in range(366)]

FREQUENCIES = {
    "daily": (Frequency(STARTED_ON, HabitFrequencyKind.DAILY),),
    "weekly": (Frequency(STARTED_ON, HabitFrequencyKind.WEEKLY, times_per_week=3),),
    "versions": (
        Frequency(STARTED_ON, HabitFrequencyKind.DAILY),
        Frequency(STARTED_ON + timedelta(days=120), HabitFrequencyKind.WEEKDAYS, None, (0, 2, 4)),
        Frequency(STARTED_ON + timedelta(days=243), HabitFrequencyKind.WEEKLY, times_per_week=4),
    ),
}
PAUSES = (
    Pause(STARTED_ON + timedelta(days=60), STARTED_ON + timedelta(days=74)),
    Pause(STARTED_ON + timedelta(days=200), STARTED_ON + timedelta(days=210)),
)
# A year of a quantity habit, met about two days out of three.
ENTRIES = {day: 2_000 if i % 3 else 1_250 for i, day in enumerate(DAYS) if i % 7 != 6}


def habit(frequency: str) -> Habit:
    return Habit(STARTED_ON, "quantity", 2_000, FREQUENCIES[frequency], PAUSES, ENTRIES)


@pytest.mark.parametrize("frequency", list(FREQUENCIES))
def test_stats_for_a_year(benchmark: BenchmarkFixture, frequency: str) -> None:
    subject = habit(frequency)

    @benchmark
    def run() -> None:
        found = rules.units(subject, TODAY)
        rules.streaks(found)
        rules.rate_percent(found, rules.frequency_for(subject.frequencies, TODAY), TODAY)
        rules.current_week(found, TODAY)
        rules.scheduled_today(found, TODAY)


def test_calendar_for_a_year(benchmark: BenchmarkFixture) -> None:
    subject = habit("versions")

    @benchmark
    def run() -> None:
        for day in DAYS:
            rules.day_status(subject, day, TODAY)


def test_clean_time(benchmark: BenchmarkFixture) -> None:
    now = datetime(2026, 11, 17, 21, tzinfo=UTC)
    relapses = [now - timedelta(days=3 * i, hours=i % 9) for i in range(120)]
    benchmark(rules.clean, STARTED_ON - timedelta(days=30), relapses, now, SP)
