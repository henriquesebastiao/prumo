from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from prumo.modules.reading import rules
from prumo.modules.reading.models import BookStatus
from prumo.modules.reading.rules import ProgressPoint

NOW = datetime(2026, 11, 17, 17, 30, tzinfo=UTC)
TODAY = date(2026, 11, 17)
SP = ZoneInfo("America/Sao_Paulo")


def at(day: int, month: int = 11, hour: int = 12) -> datetime:
    return datetime(2026, month, day, hour, tzinfo=UTC)


def change(status: BookStatus, page: int) -> rules.PageChange:
    return rules.after_page(
        status=status, page=page, total_pages=425, started_on=None, finished_on=None, today=TODAY
    )


def test_page_moves_the_status() -> None:
    assert change(BookStatus.WANT_TO_READ, 10) == rules.PageChange(BookStatus.READING, TODAY, None)
    assert change(BookStatus.READING, 425) == rules.PageChange(BookStatus.READ, TODAY, TODAY)
    assert change(BookStatus.READING, 100) == rules.PageChange(BookStatus.READING, None, None)
    assert change(BookStatus.WANT_TO_READ, 0).status == BookStatus.WANT_TO_READ


def test_progress_percent_reaches_100_only_at_the_end() -> None:
    assert rules.progress_percent(212, 425) == 50
    assert rules.progress_percent(424, 425) == 99
    assert rules.progress_percent(425, 425) == 100
    assert rules.progress_percent(0, 425) == 0


def test_pace_over_the_last_two_weeks() -> None:
    points = [
        ProgressPoint(at(1), 62, 0),
        ProgressPoint(at(5), 100, 62),
        ProgressPoint(at(15), 212, 100),
    ]
    assert rules.pace(points, 212, NOW) == round(150 / 14, 1)
    # Started inside the window: divided by the days since the first record.
    started = [ProgressPoint(at(10, hour=17), 50, 0)]
    assert rules.pace(started, 50, NOW) == round(50 / 7.02, 1)
    # A starting point (no pages advanced) or nothing recent gives no pace.
    assert rules.pace([ProgressPoint(at(15), 100, 100)], 100, NOW) is None
    assert rules.pace([ProgressPoint(at(1, month=10), 80, 0)], 80, NOW) is None
    assert rules.pace([], 0, NOW) is None


def test_forecast() -> None:
    def forecast(status: BookStatus, pace: float | None) -> date | None:
        return rules.forecast(status=status, remaining_pages=213, pages_per_day=pace, today=TODAY)

    assert forecast(BookStatus.READING, 10.7) == date(2026, 12, 7)
    assert forecast(BookStatus.READ, 10.7) is None
    assert forecast(BookStatus.READING, None) is None


def test_weekly_pages_fill_the_gaps() -> None:
    points = [
        ProgressPoint(at(27, month=10), 30, 0),
        ProgressPoint(at(29, month=10), 62, 30),
        ProgressPoint(at(14), 141, 62),
        # 00:30 UTC on Monday 16/11 is still Sunday 15/11 in São Paulo.
        ProgressPoint(datetime(2026, 11, 16, 0, 30, tzinfo=UTC), 212, 141),
    ]
    assert rules.weekly_pages(points, SP) == [
        (date(2026, 10, 26), 62),
        (date(2026, 11, 2), 0),
        (date(2026, 11, 9), 150),
    ]
    assert rules.weekly_pages([ProgressPoint(at(1), 10, 10)], SP) == []
