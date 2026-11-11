from datetime import UTC, date, datetime, time, timedelta
from uuid import uuid7
from zoneinfo import ZoneInfo

from prumo.modules.studies import rules
from prumo.modules.studies.rules import Block, DayStatus, Session

SP = ZoneInfo("America/Sao_Paulo")
TODAY = date(2026, 11, 17)  # Tuesday
CALC, FASTAPI = uuid7(), uuid7()


def at(value: str) -> datetime:
    """A local São Paulo moment."""
    return datetime.fromisoformat(f"{value}-03:00")


def test_the_plan_in_force_is_the_latest_version_started() -> None:
    old = [Block(CALC, (0,), None, 30)]
    new = [Block(CALC, (0,), None, 60)]
    versions = [(date(2026, 10, 5), old), (date(2026, 11, 2), new), (date(2026, 11, 23), [])]
    assert rules.plan_for(versions, date(2026, 10, 20)) == old
    assert rules.plan_for(versions, date(2026, 11, 2)) == new
    assert rules.plan_for(versions, date(2026, 11, 30)) == []
    assert rules.plan_for(versions, date(2026, 9, 1)) == ()


def test_the_goal_sums_the_blocks_of_the_weekday_and_the_time_only_orders() -> None:
    blocks = [
        Block(CALC, (0, 2), time(19), 60),
        Block(CALC, (2,), time(7), 30),
        Block(FASTAPI, (1, 3), None, 45),
    ]
    rows = rules.subject_days(blocks, [], date(2026, 11, 18), TODAY, SP)  # Wednesday
    assert [(r.subject_id, r.goal_minutes) for r in rows] == [(CALC, 90)]
    assert [b.starts_at for b in rows[0].blocks] == [time(7), time(19)]


def test_a_session_counts_on_the_local_day_it_started() -> None:
    sessions = [
        Session(CALC, at("2026-11-10T23:30:00"), 60),  # 02:30 UTC of the 11th
        Session(CALC, at("2026-11-11T08:00:00"), 20),
    ]
    assert rules.done(sessions, date(2026, 11, 10), SP) == {CALC: 60}
    assert rules.done(sessions, date(2026, 11, 11), SP) == {CALC: 20}
    assert rules.done(sessions, date(2026, 11, 11), ZoneInfo("UTC")) == {CALC: 80}


def test_every_status_of_a_subject_on_a_day() -> None:
    past, future = date(2026, 11, 16), date(2026, 11, 18)
    assert rules.status(60, 60, past, TODAY) == DayStatus.MET
    assert rules.status(60, 90, past, TODAY) == DayStatus.MET
    assert rules.status(60, 20, past, TODAY) == DayStatus.PARTIAL
    assert rules.status(60, 0, past, TODAY) == DayStatus.MISSED
    assert rules.status(60, 0, TODAY, TODAY) == DayStatus.IN_PROGRESS
    assert rules.status(60, 20, TODAY, TODAY) == DayStatus.PARTIAL
    assert rules.status(60, 0, future, TODAY) == DayStatus.IN_PROGRESS
    assert rules.status(0, 15, past, TODAY) == DayStatus.EXTRA
    assert rules.status(0, 0, past, TODAY) is None


def test_archived_subjects_leave_the_day_and_a_day_without_goals_does_not_count() -> None:
    blocks = [Block(CALC, (0,), None, 60), Block(FASTAPI, (0,), None, 45)]
    monday = date(2026, 11, 16)
    sessions = [Session(FASTAPI, at("2026-11-16T20:00:00"), 45)]
    rows = rules.subject_days(blocks, sessions, monday, TODAY, SP, hidden=[CALC])
    assert [r.subject_id for r in rows] == [FASTAPI]
    assert rules.day_met(rows) is True
    assert rules.day_met(rules.subject_days(blocks, sessions, monday, TODAY, SP)) is False
    assert rules.day_met([]) is None
    extra = rules.subject_days([], sessions, monday, TODAY, SP)
    assert extra[0].status == DayStatus.EXTRA
    assert rules.day_met(extra) is None


def test_the_current_week_counts_planned_days_only_up_to_today() -> None:
    blocks = [Block(CALC, (0, 1, 2, 3, 4), None, 30)]
    sessions = [Session(CALC, at("2026-11-16T07:00:00"), 30)]
    monday = date(2026, 11, 16)
    days = {
        monday + timedelta(days=i): rules.subject_days(
            blocks, sessions, monday + timedelta(days=i), TODAY, SP
        )
        for i in range(7)
    }
    totals = rules.week_totals(days, TODAY)
    assert (totals.days_met, totals.days_planned) == (1, 2)
    assert (totals.minutes_done, totals.minutes_planned) == (30, 150)


def test_weekly_minutes_cover_the_last_eight_weeks_including_the_current() -> None:
    sessions = [
        Session(CALC, at("2026-11-17T08:00:00"), 30),
        Session(CALC, at("2026-11-09T08:00:00"), 45),
        Session(CALC, at("2026-09-01T08:00:00"), 500),  # before the window
    ]
    weeks = rules.weekly_minutes(sessions, TODAY, SP)
    assert len(weeks) == 8
    assert weeks[0][0] == date(2026, 9, 28)
    assert weeks[-2:] == [(date(2026, 11, 9), 45), (date(2026, 11, 16), 30)]
    assert sum(m for _, m in weeks) == 75


def test_only_obsidian_links_are_accepted() -> None:
    assert rules.valid_obsidian_uri("obsidian://open?vault=Estudos&file=Dev%2FFastAPI")
    assert not rules.valid_obsidian_uri("https://obsidian.md")
    assert not rules.valid_obsidian_uri("obsidian://")


def test_utc_and_local_days_agree_at_noon() -> None:
    assert rules.local_day(datetime(2026, 11, 17, 15, tzinfo=UTC), SP) == TODAY
