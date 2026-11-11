from datetime import date, datetime, time
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from prumo.core.db import Base, IdMixin, TimestampMixin, UserOwnedMixin


class StudyArea(Base, IdMixin, TimestampMixin, UserOwnedMixin):
    __tablename__ = "studies_areas"

    name: Mapped[str] = mapped_column(String(60))
    color: Mapped[str] = mapped_column(String(16))
    archived_at: Mapped[datetime | None]


class Subject(Base, IdMixin, TimestampMixin, UserOwnedMixin):
    __tablename__ = "studies_subjects"
    __table_args__ = (Index("ix_studies_subjects_user_area", "user_id", "area_id"),)

    area_id: Mapped[UUID] = mapped_column(ForeignKey("studies_areas.id", ondelete="RESTRICT"))
    name: Mapped[str] = mapped_column(String(60))
    obsidian_uri: Mapped[str | None] = mapped_column(String(512))
    archived_at: Mapped[datetime | None]


class Topic(Base, IdMixin, TimestampMixin, UserOwnedMixin):
    __tablename__ = "studies_topics"
    subject_id: Mapped[UUID] = mapped_column(ForeignKey("studies_subjects.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(80))

    # E10: unique in the subject regardless of case.
    __table_args__ = (
        Index("uq_studies_topics_subject_name", subject_id, func.lower(name), unique=True),
    )


class StudyPlan(Base, IdMixin, TimestampMixin, UserOwnedMixin):
    __tablename__ = "studies_plans"
    __table_args__ = (
        UniqueConstraint("user_id", "valid_from", name="uq_studies_plans_valid_from"),
    )

    valid_from: Mapped[date]


class PlanBlock(Base, IdMixin, TimestampMixin, UserOwnedMixin):
    __tablename__ = "studies_plan_blocks"
    __table_args__ = (
        Index("ix_studies_plan_blocks_plan", "plan_id"),
        CheckConstraint("duration_minutes BETWEEN 1 AND 720", name="duration_range"),
    )

    plan_id: Mapped[UUID] = mapped_column(ForeignKey("studies_plans.id", ondelete="CASCADE"))
    subject_id: Mapped[UUID] = mapped_column(ForeignKey("studies_subjects.id", ondelete="CASCADE"))
    # 0 = Monday … 6 = Sunday, as `date.weekday()`.
    weekdays: Mapped[list[int]] = mapped_column(ARRAY(SmallInteger))
    starts_at: Mapped[time | None]
    duration_minutes: Mapped[int]


class StudySession(Base, IdMixin, TimestampMixin, UserOwnedMixin):
    __tablename__ = "studies_sessions"
    __table_args__ = (
        Index("ix_studies_sessions_user_time", "user_id", "started_at"),
        Index("ix_studies_sessions_subject_time", "subject_id", "started_at"),
        CheckConstraint("duration_minutes BETWEEN 1 AND 720", name="duration_range"),
    )

    subject_id: Mapped[UUID] = mapped_column(ForeignKey("studies_subjects.id", ondelete="CASCADE"))
    topic_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("studies_topics.id", ondelete="SET NULL")
    )
    started_at: Mapped[datetime]
    duration_minutes: Mapped[int]
