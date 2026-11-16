from datetime import date, datetime, time
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from prumo.core.db import Base, IdMixin, TimestampMixin, UserOwnedMixin


class Habit(Base, IdMixin, TimestampMixin, UserOwnedMixin):
    __tablename__ = "habits_habits"
    __table_args__ = (
        CheckConstraint("kind IN ('build', 'quit')", name="kind"),
        CheckConstraint("target_value IS NULL OR target_value > 0", name="target_positive"),
    )

    name: Mapped[str] = mapped_column(String(60))
    # `build` (to practice) or `quit` (to stop); it never changes.
    kind: Mapped[str] = mapped_column(String(8))
    color: Mapped[str] = mapped_column(String(16))
    icon: Mapped[str] = mapped_column(String(32))
    started_on: Mapped[date]
    # Only in `build`: `check` or `quantity`, with the daily target and its unit in `quantity`.
    measure: Mapped[str | None] = mapped_column(String(10))
    target_value: Mapped[int | None]
    unit: Mapped[str | None] = mapped_column(String(12))
    archived_at: Mapped[datetime | None]
    # Wall-clock time in the user's zone, only for ordering and display (D48); null without one.
    time_of_day: Mapped[time | None]
    # The manual order of the user's habits (H10); a new habit goes last.
    position: Mapped[int] = mapped_column(default=0, server_default="0")


class HabitFrequency(Base, IdMixin, TimestampMixin, UserOwnedMixin):
    __tablename__ = "habits_frequencies"
    __table_args__ = (
        UniqueConstraint("habit_id", "valid_from", name="uq_habits_frequencies_valid_from"),
        CheckConstraint(
            "kind IN ('daily', 'weekdays', 'month_days', 'month_weekday', 'per_period')",
            name="kind",
        ),
        CheckConstraint("every_n >= 1", name="every_n_positive"),
        CheckConstraint(
            "period IS NULL OR period IN ('week', 'fortnight', 'month')", name="period"
        ),
    )

    habit_id: Mapped[UUID] = mapped_column(ForeignKey("habits_habits.id", ondelete="CASCADE"))
    valid_from: Mapped[date]
    kind: Mapped[str] = mapped_column(String(16))
    # `per_period`: `times` days met in each `period` (`week`, `fortnight`, `month`), with an
    # optional `preferred_day` (a weekday, or a day of the month in `month`) for display only.
    times: Mapped[int | None] = mapped_column(SmallInteger)
    period: Mapped[str | None] = mapped_column(String(10))
    preferred_day: Mapped[int | None] = mapped_column(SmallInteger)
    # 0 = Monday … 6 = Sunday, as `date.weekday()`.
    weekdays: Mapped[list[int] | None] = mapped_column(ARRAY(SmallInteger))
    # Every N weeks in `weekdays`, every N months in `month_days` and `month_weekday`.
    every_n: Mapped[int] = mapped_column(SmallInteger, default=1, server_default="1")
    month_days: Mapped[list[int] | None] = mapped_column(ARRAY(SmallInteger))
    month_last_day: Mapped[bool] = mapped_column(default=False, server_default="false")
    # `month_weekday`: the 1st to 4th or the last (-1) `weekday` of the month.
    week_of_month: Mapped[int | None] = mapped_column(SmallInteger)
    weekday: Mapped[int | None] = mapped_column(SmallInteger)


class HabitEntry(Base, IdMixin, TimestampMixin, UserOwnedMixin):
    """A marked day (H1). The API calls the day `on`; one entry per habit and day."""

    __tablename__ = "habits_entries"
    __table_args__ = (
        UniqueConstraint("habit_id", "day", name="uq_habits_entries_day"),
        Index("ix_habits_entries_user_day", "user_id", "day"),
        CheckConstraint("value >= 0", name="value_positive"),
    )

    habit_id: Mapped[UUID] = mapped_column(ForeignKey("habits_habits.id", ondelete="CASCADE"))
    day: Mapped[date]
    value: Mapped[int]


class HabitPause(Base, IdMixin, TimestampMixin, UserOwnedMixin):
    __tablename__ = "habits_pauses"
    __table_args__ = (
        Index("ix_habits_pauses_habit", "habit_id"),
        CheckConstraint("ends_on IS NULL OR ends_on >= starts_on", name="ends_after_start"),
    )

    habit_id: Mapped[UUID] = mapped_column(ForeignKey("habits_habits.id", ondelete="CASCADE"))
    starts_on: Mapped[date]
    ends_on: Mapped[date | None]


class Relapse(Base, IdMixin, TimestampMixin, UserOwnedMixin):
    __tablename__ = "habits_relapses"
    __table_args__ = (Index("ix_habits_relapses_habit_time", "habit_id", "occurred_at"),)

    habit_id: Mapped[UUID] = mapped_column(ForeignKey("habits_habits.id", ondelete="CASCADE"))
    occurred_at: Mapped[datetime]
    note: Mapped[str | None] = mapped_column(String(500))
