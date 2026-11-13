"""Studies rules (E1-E7): plans, daily goals, week totals and weekly minutes."""

from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from pytest_codspeed import BenchmarkFixture

from prumo.modules.studies import rules
from prumo.modules.studies.rules import Block, Session

SP = ZoneInfo("America/Sao_Paulo")
TODAY = date(2026, 11, 17)  # Tuesday
SUBJECTS = [UUID(int=i) for i in range(1, 9)]

BLOCKS = [
    Block(subject, ((i + offset) % 7, (i + offset + 3) % 7), time(7 + offset * 2), 30 + 15 * offset)
    for i, subject in enumerate(SUBJECTS)
    for offset in range(3)
]
PLANS = [(TODAY - timedelta(weeks=8 * v), BLOCKS[: 8 + 2 * v]) for v in range(8)]
# Eight weeks of sessions, a few per day.
SESSIONS = [
    Session(
        SUBJECTS[i % len(SUBJECTS)],
        datetime(2026, 11, 17, 23, tzinfo=UTC) - timedelta(hours=7 * i),
        25 + (i * 11) % 60,
    )
    for i in range(8 * 7 * 3)
]
WEEK = [rules.week_start(TODAY) + timedelta(days=i) for i in range(7)]


def test_week_view(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def run() -> None:
        days = {}
        for day in WEEK:
            blocks = rules.plan_for(PLANS, day)
            days[day] = rules.subject_days(blocks, SESSIONS, day, TODAY, SP, hidden=SUBJECTS[-1:])
        rules.week_totals(days, TODAY)


def test_weekly_minutes(benchmark: BenchmarkFixture) -> None:
    benchmark(rules.weekly_minutes, SESSIONS, TODAY, SP)
