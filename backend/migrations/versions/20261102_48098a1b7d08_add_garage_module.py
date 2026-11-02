"""add garage module

Revision ID: 48098a1b7d08
Revises: c2c25c918852
Create Date: 2026-11-02 14:28:45.284314
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "48098a1b7d08"
down_revision: str | None = "c2c25c918852"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "garage_vehicles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "kind",
            sa.Enum(
                "car",
                "motorcycle",
                name="vehicle_kind",
                native_enum=False,
                create_constraint=True,
                length=24,
            ),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("brand", sa.String(length=60), nullable=False),
        sa.Column("model", sa.String(length=60), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column(
            "fuel_type",
            sa.Enum(
                "gasoline",
                "gasoline_additive",
                "gasoline_premium",
                "ethanol",
                "diesel",
                "cng",
                name="fuel_type",
                native_enum=False,
                create_constraint=True,
                length=24,
            ),
            nullable=True,
        ),
        sa.Column("current_km", sa.Integer(), nullable=False),
        sa.Column("current_km_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("oil_interval_km", sa.Integer(), nullable=True),
        sa.Column("oil_interval_months", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("current_km >= 0", name=op.f("ck_garage_vehicles_current_km_positive")),
        sa.CheckConstraint(
            "oil_interval_km IS NULL OR oil_interval_km > 0",
            name=op.f("ck_garage_vehicles_oil_km_positive"),
        ),
        sa.CheckConstraint(
            "oil_interval_months IS NULL OR oil_interval_months > 0",
            name=op.f("ck_garage_vehicles_oil_months_positive"),
        ),
        sa.CheckConstraint(
            "year BETWEEN 1900 AND 2100", name=op.f("ck_garage_vehicles_year_range")
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_garage_vehicles_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_garage_vehicles")),
    )
    op.create_index(
        op.f("ix_garage_vehicles_user_id"), "garage_vehicles", ["user_id"], unique=False
    )
    op.create_table(
        "garage_workshops",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_garage_workshops_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_garage_workshops")),
    )
    op.create_index(
        op.f("ix_garage_workshops_user_id"), "garage_workshops", ["user_id"], unique=False
    )
    op.create_index(
        "uq_garage_workshops_user_name",
        "garage_workshops",
        ["user_id", sa.text("lower(name)")],
        unique=True,
    )
    op.create_table(
        "garage_fuelings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("vehicle_id", sa.Uuid(), nullable=False),
        sa.Column("fueled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("km", sa.Integer(), nullable=False),
        sa.Column(
            "fuel_type",
            sa.Enum(
                "gasoline",
                "gasoline_additive",
                "gasoline_premium",
                "ethanol",
                "diesel",
                "cng",
                name="fueling_fuel_type",
                native_enum=False,
                create_constraint=True,
                length=24,
            ),
            nullable=False,
        ),
        sa.Column("volume_ml", sa.Integer(), nullable=False),
        sa.Column("total_cents", sa.Integer(), nullable=False),
        sa.Column("full_tank", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("km >= 0", name=op.f("ck_garage_fuelings_km_positive")),
        sa.CheckConstraint("total_cents > 0", name=op.f("ck_garage_fuelings_total_positive")),
        sa.CheckConstraint("volume_ml > 0", name=op.f("ck_garage_fuelings_volume_positive")),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_garage_fuelings_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["vehicle_id"],
            ["garage_vehicles.id"],
            name=op.f("fk_garage_fuelings_vehicle_id_garage_vehicles"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_garage_fuelings")),
    )
    op.create_index(
        op.f("ix_garage_fuelings_user_id"), "garage_fuelings", ["user_id"], unique=False
    )
    op.create_index(
        "ix_garage_fuelings_vehicle_time",
        "garage_fuelings",
        ["vehicle_id", "fueled_at"],
        unique=False,
    )
    op.create_table(
        "garage_maintenances",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("vehicle_id", sa.Uuid(), nullable=False),
        sa.Column(
            "kind",
            sa.Enum(
                "general",
                "oil_change",
                name="maintenance_kind",
                native_enum=False,
                create_constraint=True,
                length=24,
            ),
            nullable=False,
        ),
        sa.Column("performed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("km", sa.Integer(), nullable=False),
        sa.Column("workshop_id", sa.Uuid(), nullable=True),
        sa.Column("labor_cost_cents", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("oil_type", sa.String(length=120), nullable=True),
        sa.Column("next_oil_change_km", sa.Integer(), nullable=True),
        sa.Column("next_oil_change_on", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("km >= 0", name=op.f("ck_garage_maintenances_km_positive")),
        sa.CheckConstraint(
            "labor_cost_cents >= 0", name=op.f("ck_garage_maintenances_labor_positive")
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_garage_maintenances_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["vehicle_id"],
            ["garage_vehicles.id"],
            name=op.f("fk_garage_maintenances_vehicle_id_garage_vehicles"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["workshop_id"],
            ["garage_workshops.id"],
            name=op.f("fk_garage_maintenances_workshop_id_garage_workshops"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_garage_maintenances")),
    )
    op.create_index(
        op.f("ix_garage_maintenances_user_id"), "garage_maintenances", ["user_id"], unique=False
    )
    op.create_index(
        "ix_garage_maintenances_vehicle_time",
        "garage_maintenances",
        ["vehicle_id", "performed_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_garage_maintenances_workshop_id"),
        "garage_maintenances",
        ["workshop_id"],
        unique=False,
    )
    op.create_table(
        "garage_odometer_readings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("vehicle_id", sa.Uuid(), nullable=False),
        sa.Column("km", sa.Integer(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "source",
            sa.Enum(
                "manual",
                "maintenance",
                "fueling",
                name="reading_source",
                native_enum=False,
                create_constraint=True,
                length=24,
            ),
            nullable=False,
        ),
        sa.Column("source_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("km >= 0", name=op.f("ck_garage_odometer_readings_km_positive")),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_garage_odometer_readings_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["vehicle_id"],
            ["garage_vehicles.id"],
            name=op.f("fk_garage_odometer_readings_vehicle_id_garage_vehicles"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_garage_odometer_readings")),
    )
    op.create_index(
        "ix_garage_odometer_readings_source",
        "garage_odometer_readings",
        ["source", "source_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_garage_odometer_readings_user_id"),
        "garage_odometer_readings",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_garage_odometer_readings_vehicle_time",
        "garage_odometer_readings",
        ["vehicle_id", "recorded_at"],
        unique=False,
    )
    op.create_table(
        "garage_maintenance_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("maintenance_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(length=120), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price_cents", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "quantity >= 1", name=op.f("ck_garage_maintenance_items_quantity_positive")
        ),
        sa.CheckConstraint(
            "unit_price_cents >= 0", name=op.f("ck_garage_maintenance_items_price_positive")
        ),
        sa.ForeignKeyConstraint(
            ["maintenance_id"],
            ["garage_maintenances.id"],
            name=op.f("fk_garage_maintenance_items_maintenance_id_garage_maintenances"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_garage_maintenance_items_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_garage_maintenance_items")),
    )
    op.create_index(
        op.f("ix_garage_maintenance_items_maintenance_id"),
        "garage_maintenance_items",
        ["maintenance_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_garage_maintenance_items_user_id"),
        "garage_maintenance_items",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_garage_maintenance_items_user_id"), table_name="garage_maintenance_items"
    )
    op.drop_index(
        op.f("ix_garage_maintenance_items_maintenance_id"), table_name="garage_maintenance_items"
    )
    op.drop_table("garage_maintenance_items")
    op.drop_index("ix_garage_odometer_readings_vehicle_time", table_name="garage_odometer_readings")
    op.drop_index(
        op.f("ix_garage_odometer_readings_user_id"), table_name="garage_odometer_readings"
    )
    op.drop_index("ix_garage_odometer_readings_source", table_name="garage_odometer_readings")
    op.drop_table("garage_odometer_readings")
    op.drop_index(op.f("ix_garage_maintenances_workshop_id"), table_name="garage_maintenances")
    op.drop_index("ix_garage_maintenances_vehicle_time", table_name="garage_maintenances")
    op.drop_index(op.f("ix_garage_maintenances_user_id"), table_name="garage_maintenances")
    op.drop_table("garage_maintenances")
    op.drop_index("ix_garage_fuelings_vehicle_time", table_name="garage_fuelings")
    op.drop_index(op.f("ix_garage_fuelings_user_id"), table_name="garage_fuelings")
    op.drop_table("garage_fuelings")
    op.drop_index("uq_garage_workshops_user_name", table_name="garage_workshops")
    op.drop_index(op.f("ix_garage_workshops_user_id"), table_name="garage_workshops")
    op.drop_table("garage_workshops")
    op.drop_index(op.f("ix_garage_vehicles_user_id"), table_name="garage_vehicles")
    op.drop_table("garage_vehicles")
