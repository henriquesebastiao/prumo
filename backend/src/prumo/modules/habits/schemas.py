from datetime import date, datetime
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import BaseModel, Field, StringConstraints, field_validator, model_validator

from prumo.core.idempotency import ClientId
from prumo.core.modules import ModuleSummary
from prumo.core.schemas import reject_null
from prumo.modules.habits.recurrence import Cadence, HabitFrequencyKind, Period
from prumo.modules.habits.rules import CalendarStatus, StreakUnit

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
MonthDay = Annotated[int, Field(ge=1, le=31)]
WeekOfMonth = Literal[1, 2, 3, 4, -1]
TimeOfDay = Annotated[
    str,
    StringConstraints(pattern=r"^([01]\d|2[0-3]):[0-5]\d$"),
    Field(description="`HH:MM`, wall-clock time in the user's zone."),
]
HabitKind = Literal["build", "quit"]
Measure = Literal["check", "quantity"]
Month = Annotated[str, StringConstraints(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")]


# ---------------------------------------------------------------- frequencies (H2)


class HabitFrequencyFields(BaseModel):
    """The shape of each kind (H2). `weekly` with `times_per_week` is still accepted from apps
    before D48 and becomes `per_period` with `period = week`."""

    kind: HabitFrequencyKind
    weekdays: list[Weekday] | None = Field(default=None, description="In `weekdays`.")
    every_n_weeks: int | None = Field(
        default=None, ge=1, le=52, description="In `weekdays`: every N weeks; 1 by default."
    )
    month_days: list[MonthDay] | None = Field(
        default=None,
        description="In `month_days`; a day the month lacks falls on its last day.",
    )
    month_last_day: bool | None = Field(
        default=None, description="In `month_days`: the last day of the month too."
    )
    week_of_month: WeekOfMonth | None = Field(
        default=None, description="In `month_weekday`: 1 to 4, or -1 for the last."
    )
    weekday: Weekday | None = Field(default=None, description="In `month_weekday`.")
    every_n_months: int | None = Field(
        default=None,
        ge=1,
        le=12,
        description="In `month_days` and `month_weekday`: every N months; 1 by default.",
    )
    times: int | None = Field(
        default=None, ge=1, le=28, description="In `per_period`: days met in each period."
    )
    period: Period | None = Field(default=None, description="In `per_period`.")
    preferred_day: int | None = Field(
        default=None,
        ge=0,
        le=31,
        description=(
            "In `per_period`, display only: a weekday (0-6) in `week` and `fortnight`, a day of "
            "the month (1-31) in `month`."
        ),
    )
    times_per_week: int | None = Field(
        default=None, ge=1, le=7, description="Deprecated: `weekly` only; use `per_period`."
    )

    @model_validator(mode="after")
    def _shape(self) -> Self:
        kind = self.kind
        if kind == HabitFrequencyKind.WEEKLY:
            if self.times_per_week is None:
                raise ValueError("`weekly` needs times_per_week.")
            self.kind = HabitFrequencyKind.PER_PERIOD
            self.times = self.times_per_week
            self.period = Period.WEEK
            kind = self.kind
        keep: set[str] = set()
        if kind == HabitFrequencyKind.WEEKDAYS:
            if not self.weekdays:
                raise ValueError("`weekdays` needs at least one weekday.")
            if len(set(self.weekdays)) != len(self.weekdays):
                raise ValueError("Weekdays must not repeat.")
            self.weekdays = sorted(self.weekdays)
            self.every_n_weeks = self.every_n_weeks or 1
            keep = {"weekdays", "every_n_weeks"}
        elif kind == HabitFrequencyKind.MONTH_DAYS:
            days = sorted(set(self.month_days or ()))
            if not days and not self.month_last_day:
                raise ValueError("`month_days` needs a day or the last day of the month.")
            self.month_days = days
            self.month_last_day = bool(self.month_last_day)
            self.every_n_months = self.every_n_months or 1
            keep = {"month_days", "month_last_day", "every_n_months"}
        elif kind == HabitFrequencyKind.MONTH_WEEKDAY:
            if self.week_of_month is None or self.weekday is None:
                raise ValueError("`month_weekday` needs week_of_month and weekday.")
            self.every_n_months = self.every_n_months or 1
            keep = {"week_of_month", "weekday", "every_n_months"}
        elif kind == HabitFrequencyKind.PER_PERIOD:
            if self.times is None or self.period is None:
                raise ValueError("`per_period` needs times and period.")
            keep = {"times", "period", "preferred_day"}
        for name in OPTIONAL_FREQUENCY_FIELDS - keep:
            setattr(self, name, None)
        return self


OPTIONAL_FREQUENCY_FIELDS = frozenset(
    {
        "weekdays",
        "every_n_weeks",
        "month_days",
        "month_last_day",
        "week_of_month",
        "weekday",
        "every_n_months",
        "times",
        "period",
        "preferred_day",
        "times_per_week",
    }
)


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
    kind: HabitFrequencyKind = Field(description="Never `weekly` (input only, deprecated).")
    cadence: Cadence = Field(description="How often it comes back, for filters and labels.")
    weekdays: list[int] | None
    every_n_weeks: int | None
    month_days: list[int] | None
    month_last_day: bool | None
    week_of_month: int | None
    weekday: int | None
    every_n_months: int | None
    times: int | None
    period: Period | None
    preferred_day: int | None
    times_per_week: int | None = Field(description="Deprecated: `times` when `period` is `week`.")


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
    time_of_day: TimeOfDay | None = Field(default=None, description="Optional time (H10).")


class HabitUpdate(BaseModel):
    """The kind and the measure never change."""

    name: Name | None = None
    color: Color | None = None
    icon: Icon | None = None
    started_on: date | None = None
    target_value: Target | None = None
    unit: Unit | None = None
    time_of_day: TimeOfDay | None = Field(default=None, description="`null` clears it.")

    _not_null = reject_null("name", "color", "icon", "started_on", "target_value", "unit")


class HabitWeek(BaseModel):
    """H6: days met this week over what the week asks."""

    done: int
    target: int


class HabitPeriod(BaseModel):
    """H6: the `per_period` period in progress."""

    period: Period
    starts_on: date
    ends_on: date
    done: int = Field(description="Days met in the period.")
    target: int = Field(description="Days the period asks (H2).")
    days_left: int = Field(description="Days from the reference day to the end, both included.")
    neutral: bool = Field(description="H2a: out of the rate; breaks no streak.")


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
    time_of_day: str | None = Field(description="`HH:MM` in the user's zone, or null.")
    position: int = Field(description="Manual order (H10).")
    # `build`
    frequency: HabitFrequencyRead | None = Field(description="The version in force today.")
    paused: bool = Field(description="Today is in a pause.")
    rate_percent: int | None = Field(description="H5; null with nothing scheduled.")
    current_streak: int | None = Field(description="H4, in days or weeks (`streak_unit`).")
    best_streak: int | None
    streak_unit: StreakUnit | None = Field(
        description="`day` (daily or weekly fixed dates), `occurrence` (sparser fixed dates) or "
        "the period of `per_period`."
    )
    week: HabitWeek | None = Field(description="Deprecated: H6 when the period is a week.")
    period: HabitPeriod | None = Field(description="H6, in `per_period`.")
    next_due: date | None = Field(description="The next day that asks something; null if none.")
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
    time_of_day: str | None = Field(description="`HH:MM`, or null.")


class HabitTodayItem(BaseModel):
    habit: HabitRef
    done: bool = Field(description="H1: today is met.")
    value: int | None
    week: HabitWeek | None = Field(description="In `weekly`.")
    settled: bool = Field(description="Nothing left for today: today met, or the week met.")


class HabitsToday(BaseModel):
    """Deprecated: `GET /habits/day` groups and orders the day (H9)."""

    today: date
    items: list[HabitTodayItem] = Field(description="Without archived nor paused habits.")
    done: int
    scheduled: int


Promotion = Literal["preferred_day", "due_soon"]


class HabitDayItem(HabitTodayItem):
    """A habit of a day (H9), with its time, its period and why a period rose to the day."""

    late: bool = Field(description="Open with a time already past (only today).")
    period: HabitPeriod | None = Field(description="In `per_period`, from the day of the view.")
    promoted: Promotion | None = Field(
        description="Why a `per_period` habit is in the day: its preferred day came, or few days "
        "are left."
    )
    due_in_days: int | None = Field(description="With `due_soon`: days until the period ends.")


class HabitsSummaryQuit(BaseModel):
    id: UUID
    name: str
    color: str
    icon: str
    clean_days: int


class HabitsDay(BaseModel):
    """A day of habits (H9), grouped and ordered by the server (H10)."""

    on: date
    today: date
    now: str | None = Field(description="`HH:MM` in the user's zone, only when `on` is today.")
    done: int = Field(description="Met on the day: `done_items`.")
    scheduled: int = Field(description="`timeline`, `untimed` and `done_items`.")
    timeline: list[HabitDayItem] = Field(description="Open, with a time, by time.")
    untimed: list[HabitDayItem] = Field(description="Open, without a time, in the manual order.")
    period: list[HabitDayItem] = Field(
        description="`per_period` still open in their period and not promoted to the day."
    )
    done_items: list[HabitDayItem] = Field(description="Met on the day, in the same order.")
    quit: list[HabitsSummaryQuit] = Field(description="Habits to quit, with the days without.")


class HabitOrder(BaseModel):
    """The new order of some habits: they take, in this order, the places they held (H10)."""

    ids: list[UUID] = Field(min_length=1, max_length=500)

    @field_validator("ids")
    @classmethod
    def _unique(cls, value: list[UUID]) -> list[UUID]:
        if len(set(value)) != len(value):
            raise ValueError("Ids must not repeat.")
        return value


class HabitsSummary(ModuleSummary):
    module: Literal["habits"] = "habits"
    today: date
    done_today: int
    scheduled_today: int
    pending: list[HabitRef] = Field(description="Up to 3 habits still open today.")
    upcoming: list[HabitDayItem] = Field(
        description="Up to 5 open today, in the order of the day (timeline, then untimed)."
    )
    pending_more: int = Field(description="Open ones beyond `pending`.")
    quit: list[HabitsSummaryQuit]
