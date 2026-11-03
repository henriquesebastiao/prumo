"""Pure calculations of the reading rules (no database). See docs/dominio.md, R3-R9."""

import math
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from prumo.modules.reading.models import BookStatus

PACE_WINDOW = timedelta(days=14)
MAX_WEEKS = 8


@dataclass(frozen=True)
class PageChange:
    status: BookStatus
    started_on: date | None
    finished_on: date | None


def after_page(
    *,
    status: BookStatus,
    page: int,
    total_pages: int,
    started_on: date | None,
    finished_on: date | None,
    today: date,
) -> PageChange:
    """R3 and R4: the status and dates of a book after its current page changes."""
    if page >= total_pages:
        return PageChange(BookStatus.READ, started_on or today, finished_on or today)
    if page > 0 and status == BookStatus.WANT_TO_READ:
        return PageChange(BookStatus.READING, started_on or today, finished_on)
    return PageChange(status, started_on, finished_on)


def progress_percent(current_page: int, total_pages: int) -> int:
    """R5: rounded, and 100 only when the book is finished."""
    if not total_pages:
        return 0
    value = round(current_page * 100 / total_pages)
    return value if current_page >= total_pages else min(value, 99)


@dataclass(frozen=True)
class ProgressPoint:
    recorded_at: datetime
    page: int
    previous_page: int


def pace(points: Sequence[ProgressPoint], current_page: int, now: datetime) -> float | None:
    """R7: pages per day over the last 14 days. `points` in chronological order."""
    if not points:
        return None
    start = now - PACE_WINDOW
    before = [p for p in points if p.recorded_at < start]
    inside = [p for p in points if p.recorded_at >= start]
    if not inside:
        return None
    baseline = before[-1].page if before else inside[0].previous_page
    advanced = current_page - baseline
    if advanced <= 0:
        return None
    since = start if before else inside[0].recorded_at
    days = max(1.0, (now - since) / timedelta(days=1))
    return round(advanced / min(days, PACE_WINDOW.days), 1)


def forecast(
    *, status: BookStatus, remaining_pages: int, pages_per_day: float | None, today: date
) -> date | None:
    """R8."""
    if status != BookStatus.READING or not pages_per_day or remaining_pages <= 0:
        return None
    return today + timedelta(days=math.ceil(remaining_pages / pages_per_day))


def week_start(day: date) -> date:
    return day - timedelta(days=day.weekday())


def weekly_pages(points: Sequence[ProgressPoint], tz: ZoneInfo) -> list[tuple[date, int]]:
    """R9: pages advanced per week (Monday to Sunday), first to last week with records."""
    advanced = [p for p in points if p.page != p.previous_page]
    if not advanced:
        return []
    totals: dict[date, int] = {}
    for point in advanced:
        week = week_start(point.recorded_at.astimezone(tz).date())
        totals[week] = totals.get(week, 0) + point.page - point.previous_page
    first, last = min(totals), max(totals)
    weeks = []
    week = first
    while week <= last:
        weeks.append((week, totals.get(week, 0)))
        week += timedelta(days=7)
    return weeks[-MAX_WEEKS:]
