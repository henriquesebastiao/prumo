from datetime import date, datetime, time
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field, StringConstraints, field_validator

from prumo.core.idempotency import ClientId
from prumo.core.modules import ModuleSummary
from prumo.core.schemas import reject_null
from prumo.modules.studies.rules import DayStatus

Color = Literal[
    "green", "teal", "cyan", "blue", "indigo", "violet", "pink", "red", "orange", "amber", "gray"
]
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]
TopicName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]
ObsidianUri = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=512),
    Field(description="`obsidian://…` link of the subject's note (E8); opened by the client."),
]
Minutes = Annotated[int, Field(ge=1, le=720)]
Weekday = Annotated[int, Field(ge=0, le=6, description="0 = Monday … 6 = Sunday.")]


def _unique_weekdays(value: list[int]) -> list[int]:
    if not value:
        raise ValueError("At least one weekday.")
    if len(set(value)) != len(value):
        raise ValueError("Weekdays must not repeat.")
    return sorted(value)


# ---------------------------------------------------------------- areas


class AreaCreate(BaseModel):
    id: ClientId | None = None
    name: Name
    color: Color = "blue"


class AreaUpdate(BaseModel):
    name: Name | None = None
    color: Color | None = None

    _not_null = reject_null("name", "color")


class AreaRead(BaseModel):
    id: UUID
    name: str
    color: str
    archived_at: datetime | None
    subjects_count: int
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------- subjects and topics


class SubjectRef(BaseModel):
    id: UUID
    name: str
    color: str = Field(description="The area's color.")


class TopicRef(BaseModel):
    id: UUID
    name: str


class TopicRead(TopicRef):
    sessions_count: int
    created_at: datetime


class TopicList(BaseModel):
    items: list[TopicRead]


class SubjectCreate(BaseModel):
    id: ClientId | None = None
    area_id: UUID
    name: Name
    obsidian_uri: ObsidianUri | None = None


class SubjectUpdate(BaseModel):
    area_id: UUID | None = None
    name: Name | None = None
    obsidian_uri: ObsidianUri | None = Field(default=None, description="`null` clears it.")

    _not_null = reject_null("area_id", "name")


class WeekMinutes(BaseModel):
    week_start: date = Field(description="Monday of the week.")
    minutes: int


class SubjectRead(BaseModel):
    id: UUID
    area_id: UUID
    area_name: str
    name: str
    color: str = Field(description="Inherited from the area.")
    obsidian_uri: str | None
    archived_at: datetime | None
    topics_count: int
    last_session_at: datetime | None
    minutes_this_week: int = Field(description="E6: Monday to today.")
    created_at: datetime
    updated_at: datetime


class StudySessionRead(BaseModel):
    id: UUID
    subject: SubjectRef
    topic: TopicRef | None
    started_at: datetime
    duration_minutes: int
    created_at: datetime
    updated_at: datetime


class SubjectDetail(SubjectRead):
    topics: list[TopicRead]
    weekly_minutes: list[WeekMinutes] = Field(description="E7: the last 8 weeks.")
    recent_sessions: list[StudySessionRead] = Field(description="The last 10.")


# ---------------------------------------------------------------- plans


class BlockWrite(BaseModel):
    subject_id: UUID
    weekdays: list[Weekday]
    starts_at: time | None = Field(default=None, description="Local time; only orders the day.")
    duration_minutes: Minutes

    _weekdays = field_validator("weekdays")(_unique_weekdays)


class BlockRead(BaseModel):
    id: UUID
    subject: SubjectRef
    weekdays: list[int]
    starts_at: time | None
    duration_minutes: int


class PlanWrite(BaseModel):
    """A version of the plan, in force from `valid_from` (E1)."""

    id: ClientId | None = None
    valid_from: date = Field(description="Today or later; the suggestion is next Monday.")
    blocks: list[BlockWrite]


class PlanBlocksWrite(BaseModel):
    blocks: list[BlockWrite]


PlanState = Literal["past", "current", "future"]


class PlanRead(BaseModel):
    id: UUID
    valid_from: date
    valid_until: date | None = Field(description="The day before the next version, if any.")
    state: PlanState
    blocks: list[BlockRead]
    created_at: datetime
    updated_at: datetime


class PlanList(BaseModel):
    today: date
    items: list[PlanRead] = Field(description="Newest version first.")


class PlanInForce(BaseModel):
    on: date
    today: date
    plan: PlanRead | None


# ---------------------------------------------------------------- sessions


class StudySessionCreate(BaseModel):
    id: ClientId | None = None
    subject_id: UUID
    topic_id: UUID | None = None
    topic_name: TopicName | None = Field(default=None, description="Creates the topic (E10).")
    started_at: datetime
    duration_minutes: Minutes


class StudySessionUpdate(BaseModel):
    subject_id: UUID | None = None
    topic_id: UUID | None = None
    topic_name: TopicName | None = None
    started_at: datetime | None = None
    duration_minutes: Minutes | None = None

    _not_null = reject_null("subject_id", "started_at", "duration_minutes")


# ---------------------------------------------------------------- day and week


class DayBlock(BaseModel):
    starts_at: time | None
    duration_minutes: int


class DayRow(BaseModel):
    subject: SubjectRef
    goal_minutes: int
    done_minutes: int
    status: DayStatus
    blocks: list[DayBlock]


class DayRead(BaseModel):
    on: date
    today: date
    is_today: bool
    rows: list[DayRow]
    done_minutes: int
    planned_minutes: int
    met: bool | None = Field(description="E5; null for a day without goals.")


class WeekSubject(BaseModel):
    subject: SubjectRef
    minutes_done: int
    minutes_planned: int


class WeekRead(BaseModel):
    start: date
    end: date
    today: date
    days: list[DayRead]
    days_met: int
    days_planned: int = Field(description="Only up to today in the current week (E6).")
    minutes_done: int
    minutes_planned: int
    by_subject: list[WeekSubject]
    previous_start: date
    next_start: date | None = Field(description="Not beyond the week after the current one.")


class StudiesOverview(BaseModel):
    areas_count: int
    subjects_count: int
    sessions_this_month: int
    minutes_this_month: int


# ---------------------------------------------------------------- summary


class SummaryBlock(BaseModel):
    subject: SubjectRef
    starts_at: time | None
    goal_minutes: int
    done_minutes: int
    status: DayStatus


class SummaryWeek(BaseModel):
    days_met: int
    days_planned: int
    minutes_done: int
    minutes_planned: int


class StudiesSummary(ModuleSummary):
    module: Literal["studies"] = "studies"
    today: date
    blocks_today: list[SummaryBlock]
    done_minutes_today: int
    planned_minutes_today: int
    week: SummaryWeek
