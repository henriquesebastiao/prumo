"""Pure calculations of the studies rules (no database). See docs/dominio.md, E1-E7."""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from enum import StrEnum
from uuid import UUID
from zoneinfo import ZoneInfo

MAX_WEEKS = 8


class DayStatus(StrEnum):
    MET = "met"
    PARTIAL = "partial"
    MISSED = "missed"
    IN_PROGRESS = "in_progress"
    EXTRA = "extra"


@dataclass(frozen=True)
class Block:
    subject_id: UUID
    weekdays: Sequence[int]
    starts_at: time | None
    duration_minutes: int


@dataclass(frozen=True)
class Session:
    subject_id: UUID
    started_at: datetime
    duration_minutes: int


@dataclass(frozen=True)
class SubjectDay:
    """E2-E4: one subject on one day."""

    subject_id: UUID
    goal_minutes: int
    done_minutes: int
    status: DayStatus
    blocks: tuple[Block, ...]


def week_start(day: date) -> date:
    return day - timedelta(days=day.weekday())


def local_day(moment: datetime, tz: ZoneInfo) -> date:
    """E3: the day a session counts in is the day it started, in the user's zone."""
    return moment.astimezone(tz).date()


def plan_for(plans: Iterable[tuple[date, Sequence[Block]]], day: date) -> Sequence[Block]:
    """E1: the blocks of the plan in force on `day` (the latest `valid_from` <= day)."""
    chosen: tuple[date, Sequence[Block]] | None = None
    for valid_from, blocks in plans:
        if valid_from <= day and (chosen is None or valid_from > chosen[0]):
            chosen = (valid_from, blocks)
    return chosen[1] if chosen else ()


def goals(blocks: Iterable[Block], day: date) -> dict[UUID, list[Block]]:
    """E2: the blocks of each subject that fall on `day`'s weekday, by starting time."""
    weekday = day.weekday()
    found: dict[UUID, list[Block]] = {}
    for block in blocks:
        if weekday in block.weekdays:
            found.setdefault(block.subject_id, []).append(block)
    for items in found.values():
        items.sort(key=lambda b: (b.starts_at is None, b.starts_at or time.min))
    return found


def done(sessions: Iterable[Session], day: date, tz: ZoneInfo) -> dict[UUID, int]:
    """E3: minutes studied per subject on `day`."""
    totals: dict[UUID, int] = {}
    for session in sessions:
        if local_day(session.started_at, tz) == day:
            totals[session.subject_id] = (
                totals.get(session.subject_id, 0) + session.duration_minutes
            )
    return totals


def status(goal: int, done_minutes: int, day: date, today: date) -> DayStatus | None:
    """E4; None when the subject has nothing on that day."""
    if goal > 0:
        if done_minutes >= goal:
            return DayStatus.MET
        if done_minutes > 0:
            return DayStatus.PARTIAL
        return DayStatus.IN_PROGRESS if day >= today else DayStatus.MISSED
    return DayStatus.EXTRA if done_minutes > 0 else None


def subject_days(
    blocks: Iterable[Block],
    sessions: Iterable[Session],
    day: date,
    today: date,
    tz: ZoneInfo,
    *,
    hidden: Iterable[UUID] = (),
) -> list[SubjectDay]:
    """The rows of one day (E2-E4). `hidden` subjects (archived, E9) are left out."""
    planned = goals(blocks, day)
    studied = done(sessions, day, tz)
    rows = []
    for subject_id in {*planned, *studied} - set(hidden):
        own = tuple(planned.get(subject_id, ()))
        goal = sum(block.duration_minutes for block in own)
        studied_minutes = studied.get(subject_id, 0)
        state = status(goal, studied_minutes, day, today)
        if state is None:
            continue
        rows.append(SubjectDay(subject_id, goal, studied_minutes, state, own))
    rows.sort(
        key=lambda row: (
            row.blocks[0].starts_at if row.blocks and row.blocks[0].starts_at else time.max,
            row.goal_minutes == 0,
        )
    )
    return rows


def day_met(rows: Sequence[SubjectDay]) -> bool | None:
    """E5: True when every goal of the day is met; None for a day without goals."""
    goals_of_day = [row for row in rows if row.goal_minutes > 0]
    if not goals_of_day:
        return None
    return all(row.status == DayStatus.MET for row in goals_of_day)


@dataclass(frozen=True)
class WeekTotals:
    days_met: int
    days_planned: int
    minutes_done: int
    minutes_planned: int


def week_totals(days: Mapping[date, Sequence[SubjectDay]], today: date) -> WeekTotals:
    """E6: days met over days with a goal (only up to today) and minutes done over planned."""
    days_met = days_planned = minutes_done = minutes_planned = 0
    for day, rows in days.items():
        met = day_met(rows)
        if met is not None and day <= today:
            days_planned += 1
            days_met += int(met)
        minutes_done += sum(row.done_minutes for row in rows)
        minutes_planned += sum(row.goal_minutes for row in rows)
    return WeekTotals(days_met, days_planned, minutes_done, minutes_planned)


def weekly_minutes(
    sessions: Iterable[Session], today: date, tz: ZoneInfo
) -> list[tuple[date, int]]:
    """E7: minutes per week (Monday to Sunday) over the last 8 weeks, the current one included."""
    first = week_start(today) - timedelta(weeks=MAX_WEEKS - 1)
    totals = {first + timedelta(weeks=i): 0 for i in range(MAX_WEEKS)}
    for session in sessions:
        week = week_start(local_day(session.started_at, tz))
        if week in totals:
            totals[week] += session.duration_minutes
    return sorted(totals.items())


def valid_obsidian_uri(uri: str) -> bool:
    """E8: only the scheme is checked."""
    return uri.startswith("obsidian://") and len(uri) > len("obsidian://")
