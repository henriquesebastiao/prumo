"""habits: recurrences, time of day and manual order

Hábitos (D48): fixed dates every N weeks, days of the month and the Nth weekday of the month; the
flexible `per_period` (X times a week, fortnight or month) replaces `weekly`; the optional time of
day and the manual order of the habits.

Data: every `weekly` version becomes `per_period` with `period = week`, the same `times` and
`valid_from`; the habits of each user get positions in the order of their names. Both touch
`updated_at`, so an incremental sync (D41) picks them up.

Revision ID: 5b0e3c9a7d21
Revises: 13fdf1e76a64
Create Date: 2026-11-16 09:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "5b0e3c9a7d21"
down_revision: str | None = "13fdf1e76a64"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLE = "habits_frequencies"


def upgrade() -> None:
    op.add_column("habits_habits", sa.Column("time_of_day", sa.Time(), nullable=True))
    op.add_column(
        "habits_habits",
        sa.Column("position", sa.Integer(), server_default="0", nullable=False),
    )
    op.execute(
        """
        UPDATE habits_habits AS h
        SET position = ordered.position, updated_at = now()
        FROM (
            SELECT id, row_number() OVER (
                PARTITION BY user_id ORDER BY lower(name), id
            ) - 1 AS position
            FROM habits_habits
        ) AS ordered
        WHERE h.id = ordered.id
        """
    )

    op.drop_constraint(op.f("ck_habits_frequencies_kind"), TABLE, type_="check")
    op.alter_column(TABLE, "kind", type_=sa.String(length=16), existing_nullable=False)
    op.alter_column(TABLE, "times_per_week", new_column_name="times")
    op.add_column(TABLE, sa.Column("period", sa.String(length=10), nullable=True))
    op.add_column(TABLE, sa.Column("preferred_day", sa.SmallInteger(), nullable=True))
    op.add_column(
        TABLE, sa.Column("every_n", sa.SmallInteger(), server_default="1", nullable=False)
    )
    op.add_column(
        TABLE, sa.Column("month_days", postgresql.ARRAY(sa.SmallInteger()), nullable=True)
    )
    op.add_column(
        TABLE,
        sa.Column("month_last_day", sa.Boolean(), server_default="false", nullable=False),
    )
    op.add_column(TABLE, sa.Column("week_of_month", sa.SmallInteger(), nullable=True))
    op.add_column(TABLE, sa.Column("weekday", sa.SmallInteger(), nullable=True))
    op.execute(
        f"UPDATE {TABLE} SET kind = 'per_period', period = 'week', updated_at = now() "
        "WHERE kind = 'weekly'"
    )
    op.create_check_constraint(
        op.f("ck_habits_frequencies_kind"),
        TABLE,
        "kind IN ('daily', 'weekdays', 'month_days', 'month_weekday', 'per_period')",
    )
    op.create_check_constraint(
        op.f("ck_habits_frequencies_every_n_positive"), TABLE, "every_n >= 1"
    )
    op.create_check_constraint(
        op.f("ck_habits_frequencies_period"),
        TABLE,
        "period IS NULL OR period IN ('week', 'fortnight', 'month')",
    )


def downgrade() -> None:
    # Only daily, weekdays every week and weekly periods existed before: the rest has no way back.
    op.execute(
        f"""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM {TABLE}
                WHERE kind IN ('month_days', 'month_weekday')
                   OR (kind = 'weekdays' AND every_n <> 1)
                   OR (kind = 'per_period' AND period <> 'week')
            ) THEN
                RAISE EXCEPTION 'Habit frequencies without an equivalent before D48';
            END IF;
        END $$
        """
    )
    op.drop_constraint(op.f("ck_habits_frequencies_period"), TABLE, type_="check")
    op.drop_constraint(op.f("ck_habits_frequencies_every_n_positive"), TABLE, type_="check")
    op.drop_constraint(op.f("ck_habits_frequencies_kind"), TABLE, type_="check")
    op.execute(f"UPDATE {TABLE} SET kind = 'weekly' WHERE kind = 'per_period'")
    op.drop_column(TABLE, "weekday")
    op.drop_column(TABLE, "week_of_month")
    op.drop_column(TABLE, "month_last_day")
    op.drop_column(TABLE, "month_days")
    op.drop_column(TABLE, "every_n")
    op.drop_column(TABLE, "preferred_day")
    op.drop_column(TABLE, "period")
    op.alter_column(TABLE, "times", new_column_name="times_per_week")
    op.alter_column(TABLE, "kind", type_=sa.String(length=10), existing_nullable=False)
    op.create_check_constraint(
        op.f("ck_habits_frequencies_kind"), TABLE, "kind IN ('daily', 'weekly', 'weekdays')"
    )
    op.drop_column("habits_habits", "position")
    op.drop_column("habits_habits", "time_of_day")
