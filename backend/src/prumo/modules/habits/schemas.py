from datetime import date, datetime
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import BaseModel, Field, StringConstraints, field_validator, model_validator

from prumo.core.idempotency import ClientId
from prumo.core.modules import ModuleSummary
from prumo.core.schemas import reject_null
from prumo.modules.habits.rules import CalendarStatus, HabitFrequencyKind

Color = Literal[
    "green", "teal", "cyan", "blue", "indigo", "violet", "pink", "red", "orange", "amber", "gray"
]
Icon = Annotated[
    str,
    StringConstraints(pattern=r"^[a-z0-9-]{1,32}$"),
    Field(description="Interface icon name; clients fall back to a generic icon."),
]
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]
Unit = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=12)]
Target = Annotated[int, Field(ge=1, le=100_000)]
Weekday = Annotated[int, Field(ge=0, le=6, description="0 = Monday … 6 = Sunday.")]
HabitKind = Literal["build", "quit"]
Measure = Literal["check", "quantity"]
Month = Annotated[str, StringConstraints(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")]


# ---------------------------------------------------------------- frequencies (H2)


class HabitFrequencyFields(BaseModel):
    kind: HabitFrequencyKind
    times_per_week: int | None = Field(default=None, ge=1, le=7, description="In `weekly`.")
    weekdays: list[Weekday] | None = Field(default=None, description="In `weekdays`.")

    @model_validator(mode="after")
    def _shape(self) -> Self:
        if self.kind == HabitFrequencyKind.WEEKLY:
            if self.times_per_week is None:
                raise ValueError("`weekly` needs times_per_week.")
            self.weekdays = None
        elif self.kind == HabitFrequencyKind.WEEKDAYS:
            if not self.weekdays:
                raise ValueError("`weekdays` needs at least one weekday.")
            if len(set(self.weekdays)) != len(self.weekdays):
                raise ValueError("Weekdays must not repeat.")
            self.weekdays = sorted(self.weekdays)
            self.times_per_week = None
        else:
            self.times_per_week = None
            self.weekdays = None
        return self


class HabitFrequencyCreate(HabitFrequencyFields):
    """A new version of the frequency, from `valid_from` (today or later)."""

    id: ClientId | None = None
    valid_from: date


class HabitFrequencyUpdate(HabitFrequencyFields):
    """Replaces a version that has not started yet."""


FrequencyState = Literal["past", "current", "future"]


class HabitFrequencyRead(BaseModel):
    id: UUID
    valid_from: date
    valid_until: date | None = Field(description="The day before the next version, if any.")
    state: FrequencyState
    kind: HabitFrequencyKind
    times_per_week: int | None
    weekdays: list[int] | None


# ---------------------------------------------------------------- habits


class HabitCreate(BaseModel):
    id: ClientId | None = None
    name: Name
    kind: HabitKind
    color: Color = "amber"
    icon: Icon = "sparkles"
    started_on: date | None = Field(default=None, description="Defaults to today.")
    measure: Measure | None = Field(
        default=None, description="Only in `build`; `check` by default."
    )
    target_value: Target | None = Field(default=None, description="In `quantity`.")
    unit: Unit | None = Field(default=None, description="In `quantity`: `ml`, `páginas`.")
    frequency: HabitFrequencyFields | None = Field(
        default=None, description="Only in `build`: the first version, from `started_on`."
    )


class HabitUpdate(BaseModel):
    """The kind and the measure never change."""

    name: Name | None = None
    color: Color | None = None
    icon: Icon | None = None
    started_on: date | None = None
    target_value: Target | None = None
    unit: Unit | None = None

    _not_null = reject_null("name", "color", "icon", "started_on", "target_value", "unit")


class HabitWeek(BaseModel):
    """H6: days met this week over what the week asks."""

    done: int
    target: int


class HabitTodayState(BaseModel):
    scheduled: bool = Field(description="Today asks something: its day, or the week in progress.")
    done: bool = Field(description="H1: today is met.")
    value: int | None = Field(description="Today's entry, if any.")


class HabitRead(BaseModel):
    id: UUID
    name: str
    kind: HabitKind
    color: str
    icon: str
    started_on: date
    measure: Measure | None
    target_value: int | None
    unit: str | None
    archived_at: datetime | None
    # `build`
    frequency: HabitFrequencyRead | None = Field(description="The version in force today.")
    paused: bool = Field(description="Today is in a pause.")
    rate_percent: int | None = Field(description="H5; null with nothing scheduled.")
    current_streak: int | None = Field(description="H4, in days or weeks (`streak_unit`).")
    best_streak: int | None
    streak_unit: Literal["day", "week"] | None
    week: HabitWeek | None = Field(description="H6, in `weekly`.")
    today: HabitTodayState | None
    # `quit` (H7)
    clean_since: datetime | None
    clean_days: int | None
    best_clean_days: int | None
    relapses_30d: int | None
    created_at: datetime
    updated_at: datetime


class HabitPauseRead(BaseModel):
    id: UUID
    starts_on: date
    ends_on: date | None
    created_at: datetime
    updated_at: datetime


class RelapseRead(BaseModel):
    id: UUID
    occurred_at: datetime
    note: str | None
    created_at: datetime
    updated_at: datetime


class HabitDetail(HabitRead):
    frequencies: list[HabitFrequencyRead] = Field(description="Newest version first.")
    pauses: list[HabitPauseRead] = Field(description="Newest first.")
    relapses: list[RelapseRead] = Field(description="The last 20, newest first.")


# ---------------------------------------------------------------- calendar


class HabitCalendarDay(BaseModel):
    on: date
    status: CalendarStatus
    value: int | None = Field(description="The day's entry, if any.")


class HabitCalendar(BaseModel):
    month: str = Field(description="`YYYY-MM`.")
    today: date
    days: list[HabitCalendarDay]
    previous_month: str
    next_month: str | None = Field(description="Not beyond the current month.")


# ---------------------------------------------------------------- entries (H1, H3)


class HabitEntryWrite(BaseModel):
    value: int = Field(default=1, ge=0, le=1_000_000, description="In `check`, always stored as 1.")


class HabitEntryRead(BaseModel):
    id: UUID
    habit_id: UUID
    on: date
    value: int
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------- pauses


class HabitPauseCreate(BaseModel):
    id: ClientId | None = None
    starts_on: date
    ends_on: date | None = Field(default=None, description="Open while null.")

    @model_validator(mode="after")
    def _order(self) -> Self:
        if self.ends_on is not None and self.ends_on < self.starts_on:
            raise ValueError("A pause ends on or after it starts.")
        return self


class HabitPauseUpdate(BaseModel):
    starts_on: date | None = None
    ends_on: date | None = Field(default=None, description="`null` reopens the pause.")

    _not_null = reject_null("starts_on")


# ---------------------------------------------------------------- relapses (H7)


class RelapseCreate(BaseModel):
    id: ClientId | None = None
    occurred_at: datetime
    note: Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)] | None = None

    @field_validator("note")
    @classmethod
    def _blank_is_none(cls, value: str | None) -> str | None:
        return value or None


# ---------------------------------------------------------------- today and summary (H9)


class HabitRef(BaseModel):
    id: UUID
    name: str
    color: str
    icon: str
    measure: Measure | None
    target_value: int | None
    unit: str | None


class HabitTodayItem(BaseModel):
    habit: HabitRef
    done: bool = Field(description="H1: today is met.")
    value: int | None
    week: HabitWeek | None = Field(description="In `weekly`.")
    settled: bool = Field(description="Nothing left for today: today met, or the week met.")


class HabitsToday(BaseModel):
    today: date
    items: list[HabitTodayItem] = Field(description="Without archived nor paused habits.")
    done: int
    scheduled: int


class HabitsSummaryQuit(BaseModel):
    id: UUID
    name: str
    color: str
    icon: str
    clean_days: int


class HabitsSummary(ModuleSummary):
    module: Literal["habits"] = "habits"
    today: date
    done_today: int
    scheduled_today: int
    pending: list[HabitRef] = Field(description="Up to 3 habits still open today.")
    pending_more: int = Field(description="Open ones beyond `pending`.")
    quit: list[HabitsSummaryQuit]
