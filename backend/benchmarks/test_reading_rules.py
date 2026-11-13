"""Reading rules (R3-R9): progress, pace, forecast and weekly pages."""

from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from pytest_codspeed import BenchmarkFixture

from prumo.modules.reading import rules
from prumo.modules.reading.models import BookStatus
from prumo.modules.reading.rules import ProgressPoint

SP = ZoneInfo("America/Sao_Paulo")
TODAY = date(2026, 11, 17)
NOW = datetime(2026, 11, 17, 22, tzinfo=UTC)

# A year of reading sessions, 20 pages each.
POINTS = [
    ProgressPoint(
        recorded_at=NOW - timedelta(days=365 - i, hours=i % 5),
        page=20 * (i + 1),
        previous_page=20 * i,
    )
    for i in range(365)
]


def test_pace_and_forecast(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def run() -> None:
        pages_per_day = rules.pace(POINTS, 7_300, NOW)
        rules.forecast(
            status=BookStatus.READING,
            remaining_pages=1_200,
            pages_per_day=pages_per_day,
            today=TODAY,
        )


def test_weekly_pages(benchmark: BenchmarkFixture) -> None:
    benchmark(rules.weekly_pages, POINTS, SP)


def test_page_changes(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def run() -> None:
        for page in range(0, 500, 2):
            rules.after_page(
                status=BookStatus.WANT_TO_READ,
                page=page,
                total_pages=480,
                started_on=None,
                finished_on=None,
                today=TODAY,
            )
            rules.progress_percent(page, 480)
