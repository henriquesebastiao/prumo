from datetime import date, datetime
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


class HabitFrequency(Base, IdMixin, TimestampMixin, UserOwnedMixin):
    __tablename__ = "habits_frequencies"
    __table_args__ = (
        UniqueConstraint("habit_id", "valid_from", name="uq_habits_frequencies_valid_from"),
        CheckConstraint("kind IN ('daily', 'weekly', 'weekdays')", name="kind"),
    )

    habit_id: Mapped[UUID] = mapped_column(ForeignKey("habits_habits.id", ondelete="CASCADE"))
    valid_from: Mapped[date]
    kind: Mapped[str] = mapped_column(String(10))
    times_per_week: Mapped[int | None] = mapped_column(SmallInteger)
    # 0 = Monday … 6 = Sunday, as `date.weekday()`.
    weekdays: Mapped[list[int] | None] = mapped_column(ARRAY(SmallInteger))


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
