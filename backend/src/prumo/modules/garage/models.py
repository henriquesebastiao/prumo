from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from prumo.core.db import Base, IdMixin, TimestampMixin, UserOwnedMixin, string_enum


class VehicleKind(StrEnum):
    CAR = "car"
    MOTORCYCLE = "motorcycle"


class FuelType(StrEnum):
    GASOLINE = "gasoline"
    GASOLINE_ADDITIVE = "gasoline_additive"
    GASOLINE_PREMIUM = "gasoline_premium"
    ETHANOL = "ethanol"
    DIESEL = "diesel"
    CNG = "cng"


class ReadingSource(StrEnum):
    MANUAL = "manual"
    MAINTENANCE = "maintenance"
    FUELING = "fueling"


class MaintenanceKind(StrEnum):
    GENERAL = "general"
    OIL_CHANGE = "oil_change"


class Vehicle(Base, IdMixin, TimestampMixin, UserOwnedMixin):
    __tablename__ = "garage_vehicles"
    __table_args__ = (
        CheckConstraint("year BETWEEN 1900 AND 2100", name="year_range"),
        CheckConstraint("current_km >= 0", name="current_km_positive"),
        CheckConstraint("oil_interval_km IS NULL OR oil_interval_km > 0", name="oil_km_positive"),
        CheckConstraint(
            "oil_interval_months IS NULL OR oil_interval_months > 0", name="oil_months_positive"
        ),
    )

    kind: Mapped[VehicleKind] = mapped_column(string_enum(VehicleKind, "vehicle_kind"))
    name: Mapped[str] = mapped_column(String(80))
    brand: Mapped[str] = mapped_column(String(60))
    model: Mapped[str] = mapped_column(String(60))
    year: Mapped[int]
    fuel_type: Mapped[FuelType | None] = mapped_column(string_enum(FuelType, "fuel_type"))
    # Derived from the readings (G2); kept here for fast lists.
    current_km: Mapped[int] = mapped_column(default=0)
    current_km_at: Mapped[datetime]
    oil_interval_km: Mapped[int | None]
    oil_interval_months: Mapped[int | None]
    notes: Mapped[str | None] = mapped_column(Text)
    archived_at: Mapped[datetime | None]


class OdometerReading(Base, IdMixin, TimestampMixin, UserOwnedMixin):
    __tablename__ = "garage_odometer_readings"
    __table_args__ = (
        Index("ix_garage_odometer_readings_vehicle_time", "vehicle_id", "recorded_at"),
        Index("ix_garage_odometer_readings_source", "source", "source_id"),
        CheckConstraint("km >= 0", name="km_positive"),
    )

    vehicle_id: Mapped[UUID] = mapped_column(ForeignKey("garage_vehicles.id", ondelete="CASCADE"))
    km: Mapped[int]
    recorded_at: Mapped[datetime]
    source: Mapped[ReadingSource] = mapped_column(string_enum(ReadingSource, "reading_source"))
    source_id: Mapped[UUID | None]


class Workshop(Base, IdMixin, TimestampMixin, UserOwnedMixin):
    __tablename__ = "garage_workshops"
    __table_args__ = (
        Index("uq_garage_workshops_user_name", "user_id", text("lower(name)"), unique=True),
    )

    name: Mapped[str] = mapped_column(String(80))
    notes: Mapped[str | None] = mapped_column(Text)


class Maintenance(Base, IdMixin, TimestampMixin, UserOwnedMixin):
    __tablename__ = "garage_maintenances"
    __table_args__ = (
        Index("ix_garage_maintenances_vehicle_time", "vehicle_id", "performed_at"),
        CheckConstraint("km >= 0", name="km_positive"),
        CheckConstraint("labor_cost_cents >= 0", name="labor_positive"),
    )

    vehicle_id: Mapped[UUID] = mapped_column(ForeignKey("garage_vehicles.id", ondelete="CASCADE"))
    kind: Mapped[MaintenanceKind] = mapped_column(string_enum(MaintenanceKind, "maintenance_kind"))
    performed_at: Mapped[datetime]
    km: Mapped[int]
    workshop_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("garage_workshops.id", ondelete="RESTRICT"), index=True
    )
    labor_cost_cents: Mapped[int] = mapped_column(default=0)
    notes: Mapped[str | None] = mapped_column(Text)
    oil_type: Mapped[str | None] = mapped_column(String(120))
    next_oil_change_km: Mapped[int | None]
    next_oil_change_on: Mapped[date | None]

    items: Mapped[list[MaintenanceItem]] = relationship(
        order_by="MaintenanceItem.position",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    workshop: Mapped[Workshop | None] = relationship(lazy="joined")

    @property
    def parts_cents(self) -> int:
        return sum(item.quantity * item.unit_price_cents for item in self.items)

    @property
    def total_cents(self) -> int:
        """G4: labor + sum of quantity x unit price."""
        return self.labor_cost_cents + self.parts_cents


class MaintenanceItem(Base, IdMixin, TimestampMixin, UserOwnedMixin):
    __tablename__ = "garage_maintenance_items"
    __table_args__ = (
        CheckConstraint("quantity >= 1", name="quantity_positive"),
        CheckConstraint("unit_price_cents >= 0", name="price_positive"),
    )

    maintenance_id: Mapped[UUID] = mapped_column(
        ForeignKey("garage_maintenances.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int] = mapped_column(default=0)
    description: Mapped[str] = mapped_column(String(120))
    quantity: Mapped[int] = mapped_column(default=1)
    unit_price_cents: Mapped[int]

    @property
    def total_cents(self) -> int:
        return self.quantity * self.unit_price_cents


class Fueling(Base, IdMixin, TimestampMixin, UserOwnedMixin):
    __tablename__ = "garage_fuelings"
    __table_args__ = (
        Index("ix_garage_fuelings_vehicle_time", "vehicle_id", "fueled_at"),
        CheckConstraint("km >= 0", name="km_positive"),
        CheckConstraint("volume_ml > 0", name="volume_positive"),
        CheckConstraint("total_cents > 0", name="total_positive"),
    )

    vehicle_id: Mapped[UUID] = mapped_column(ForeignKey("garage_vehicles.id", ondelete="CASCADE"))
    fueled_at: Mapped[datetime]
    km: Mapped[int]
    fuel_type: Mapped[FuelType] = mapped_column(string_enum(FuelType, "fueling_fuel_type"))
    volume_ml: Mapped[int]
    total_cents: Mapped[int]
    full_tank: Mapped[bool] = mapped_column(default=True)
    notes: Mapped[str | None] = mapped_column(Text)
