from datetime import date
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from prumo.core.deps import SessionDep
from prumo.core.errors import error_responses
from prumo.core.idempotency import create_once, created_responses
from prumo.core.pagination import Page, PageDep, UpdatedSince
from prumo.modules.habits import service
from prumo.modules.habits.models import Habit, HabitFrequency, HabitPause, Relapse
from prumo.modules.habits.schemas import (
    HabitCalendar,
    HabitCreate,
    HabitDetail,
    HabitEntryRead,
    HabitEntryWrite,
    HabitFrequencyCreate,
    HabitFrequencyRead,
    HabitFrequencyUpdate,
    HabitPauseCreate,
    HabitPauseRead,
    HabitPauseUpdate,
    HabitRead,
    HabitsToday,
    HabitUpdate,
    Month,
    RelapseCreate,
)
from prumo.system.auth.deps import CurrentUser

router = APIRouter(responses=error_responses(401, 403, 404, 422))

Archived = Annotated[
    Literal["false", "true", "all"],
    Query(description="Archived ones too (`all`) or only them (`true`)."),
]


def _habit(habit_id: UUID, session: SessionDep, user: CurrentUser) -> Habit:
    return service.get_habit(session, user, habit_id)


def _frequency(frequency_id: UUID, session: SessionDep, user: CurrentUser) -> HabitFrequency:
    return service.get_frequency(session, user, frequency_id)


def _pause(pause_id: UUID, session: SessionDep, user: CurrentUser) -> HabitPause:
    return service.get_pause(session, user, pause_id)


def _relapse(relapse_id: UUID, session: SessionDep, user: CurrentUser) -> Relapse:
    return service.get_relapse(session, user, relapse_id)


HabitDep = Annotated[Habit, Depends(_habit)]
FrequencyDep = Annotated[HabitFrequency, Depends(_frequency)]
PauseDep = Annotated[HabitPause, Depends(_pause)]
RelapseDep = Annotated[Relapse, Depends(_relapse)]


def _frequency_read(
    session: SessionDep, user: CurrentUser, frequency: HabitFrequency
) -> HabitFrequencyRead:
    habit = service.get_habit(session, user, frequency.habit_id)
    detail = service.habit_detail(session, user, habit)
    return next(f for f in detail.frequencies if f.id == frequency.id)


# ---------------------------------------------------------------- fixed paths first


@router.get("/today")
def read_today(session: SessionDep, user: CurrentUser) -> HabitsToday:
    """The habits that ask something of today, with their entry and week (H2, H6)."""
    return service.today(session, user)


@router.get("/entries")
def list_entries(
    session: SessionDep,
    user: CurrentUser,
    page: PageDep,
    habit_id: UUID | None = None,
    from_on: Annotated[date | None, Query(alias="from")] = None,
    to_on: Annotated[date | None, Query(alias="to")] = None,
    updated_since: UpdatedSince = None,
) -> Page[HabitEntryRead]:
    """Every entry, newest day first (for the app's sync)."""
    return service.list_entries(
        session,
        user,
        page,
        habit_id=habit_id,
        from_on=from_on,
        to_on=to_on,
        updated_since=updated_since,
    )


@router.patch("/frequencies/{frequency_id}")
def update_frequency(
    data: HabitFrequencyUpdate, frequency: FrequencyDep, session: SessionDep, user: CurrentUser
) -> HabitFrequencyRead:
    """Replaces a version that has not started yet."""
    service.update_frequency(session, user, frequency, data)
    return _frequency_read(session, user, frequency)


@router.delete("/frequencies/{frequency_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_frequency(frequency: FrequencyDep, session: SessionDep, user: CurrentUser) -> None:
    service.delete_frequency(session, user, frequency)


@router.patch("/pauses/{pause_id}")
def update_pause(data: HabitPauseUpdate, pause: PauseDep, session: SessionDep) -> HabitPauseRead:
    """`ends_on` ends an open pause."""
    return service.pause_read(service.update_pause(session, pause, data))


@router.delete("/pauses/{pause_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pause(pause: PauseDep, session: SessionDep) -> None:
    service.delete_pause(session, pause)


@router.delete("/relapses/{relapse_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_relapse(relapse: RelapseDep, session: SessionDep) -> None:
    service.delete_relapse(session, relapse)


# ---------------------------------------------------------------- habits


@router.get("")
def list_habits(
    session: SessionDep,
    user: CurrentUser,
    page: PageDep,
    kind: Literal["build", "quit"] | None = None,
    archived: Archived = "false",
    updated_since: UpdatedSince = None,
) -> Page[HabitRead]:
    """By name, with the derived values of each kind (H4-H7)."""
    return service.list_habits(
        session, user, page, kind=kind, archived=archived, updated_since=updated_since
    )


@router.post("", status_code=status.HTTP_201_CREATED, responses=created_responses(HabitRead))
def create_habit(
    data: HabitCreate, session: SessionDep, user: CurrentUser, response: Response
) -> HabitRead:
    habit = create_once(
        session,
        Habit,
        user.id,
        data.id,
        response,
        lambda: service.create_habit(session, user, data),
    )
    return service.habit_read(session, user, habit)


@router.get("/{habit_id}")
def read_habit(habit: HabitDep, session: SessionDep, user: CurrentUser) -> HabitDetail:
    return service.habit_detail(session, user, habit)


@router.patch("/{habit_id}")
def update_habit(
    data: HabitUpdate, habit: HabitDep, session: SessionDep, user: CurrentUser
) -> HabitRead:
    return service.habit_read(session, user, service.update_habit(session, user, habit, data))


@router.post("/{habit_id}/archive")
def archive_habit(habit: HabitDep, session: SessionDep, user: CurrentUser) -> HabitRead:
    return service.habit_read(session, user, service.set_archived(session, habit, True))


@router.post("/{habit_id}/unarchive")
def unarchive_habit(habit: HabitDep, session: SessionDep, user: CurrentUser) -> HabitRead:
    return service.habit_read(session, user, service.set_archived(session, habit, False))


@router.delete("/{habit_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_habit(habit: HabitDep, session: SessionDep) -> None:
    """Deletes the habit with its history."""
    service.delete_habit(session, habit)


@router.get("/{habit_id}/calendar")
def read_calendar(
    habit: HabitDep,
    session: SessionDep,
    user: CurrentUser,
    month: Annotated[Month | None, Query(description="`YYYY-MM`; this month by default.")] = None,
) -> HabitCalendar:
    """Each day of the month with its status; only habits to practice."""
    return service.calendar(session, user, habit, month)


@router.post(
    "/{habit_id}/frequencies",
    status_code=status.HTTP_201_CREATED,
    responses={**created_responses(HabitFrequencyRead), **error_responses(409)},
)
def create_frequency(
    data: HabitFrequencyCreate,
    habit: HabitDep,
    session: SessionDep,
    user: CurrentUser,
    response: Response,
) -> HabitFrequencyRead:
    """A new version from `valid_from` (today or later)."""
    frequency = create_once(
        session,
        HabitFrequency,
        user.id,
        data.id,
        response,
        lambda: service.create_frequency(session, user, habit, data),
    )
    return _frequency_read(session, user, frequency)


@router.put("/{habit_id}/entries/{on}")
def put_entry(
    on: date, data: HabitEntryWrite, habit: HabitDep, session: SessionDep, user: CurrentUser
) -> HabitRead:
    """Marks a day or changes its value; repeating it is safe (D47). Answers the habit."""
    return service.habit_read(session, user, service.put_entry(session, user, habit, on, data))


@router.delete("/{habit_id}/entries/{on}")
def delete_entry(on: date, habit: HabitDep, session: SessionDep, user: CurrentUser) -> HabitRead:
    """Unmarks a day. Answers the habit."""
    return service.habit_read(session, user, service.delete_entry(session, user, habit, on))


@router.post(
    "/{habit_id}/pauses",
    status_code=status.HTTP_201_CREATED,
    responses=created_responses(HabitPauseRead),
)
def create_pause(
    data: HabitPauseCreate,
    habit: HabitDep,
    session: SessionDep,
    user: CurrentUser,
    response: Response,
) -> HabitPauseRead:
    pause = create_once(
        session,
        HabitPause,
        user.id,
        data.id,
        response,
        lambda: service.create_pause(session, user, habit, data),
    )
    return service.pause_read(pause)


@router.post(
    "/{habit_id}/relapses",
    status_code=status.HTTP_201_CREATED,
    responses=created_responses(HabitRead),
)
def create_relapse(
    data: RelapseCreate, habit: HabitDep, session: SessionDep, user: CurrentUser, response: Response
) -> HabitRead:
    """Answers the habit, with its new time without (H7)."""
    create_once(
        session,
        Relapse,
        user.id,
        data.id,
        response,
        lambda: service.create_relapse(session, user, habit, data),
    )
    return service.habit_read(session, user, habit)
