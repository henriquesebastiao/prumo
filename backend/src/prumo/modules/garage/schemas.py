from datetime import date, datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator
from pydantic_core import PydanticCustomError

from prumo.core.idempotency import ClientId
from prumo.core.modules import ModuleSummary
from prumo.core.schemas import reject_null
from prumo.modules.garage.models import FuelType, MaintenanceKind, ReadingSource, VehicleKind

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]
ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]
Notes = Annotated[str, StringConstraints(strip_whitespace=True, max_length=4000)]
OilType = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
Km = Annotated[int, Field(ge=0, le=9_999_999)]
Year = Annotated[int, Field(ge=1900, le=2100)]
Cents = Annotated[int, Field(ge=0, le=10_000_000_000)]

OilState = Literal["ok", "due_soon", "overdue", "unknown"]
Criterion = Literal["km", "date"]


class VehicleRef(BaseModel):
    id: UUID
    name: str
    kind: VehicleKind


# ---------------------------------------------------------------- vehicles


class VehicleCreate(BaseModel):
    id: ClientId | None = None
    kind: VehicleKind
    name: Name = Field(description="Nickname shown in Prumo.")
    brand: ShortText
    model: ShortText
    year: Year
    fuel_type: FuelType | None = Field(default=None, description="Usual fuel (pre-selected).")
    current_km: Km = Field(description="Odometer at registration; creates the first reading.")
    oil_interval_km: Annotated[int, Field(gt=0, le=1_000_000)] | None = None
    oil_interval_months: Annotated[int, Field(gt=0, le=120)] | None = None
    notes: Notes | None = None


class VehicleUpdate(BaseModel):
    kind: VehicleKind | None = None
    name: Name | None = None
    brand: ShortText | None = None
    model: ShortText | None = None
    year: Year | None = None
    fuel_type: FuelType | None = None
    current_km: Km | None = Field(
        default=None, description="A different value records a manual reading now."
    )
    oil_interval_km: Annotated[int, Field(gt=0, le=1_000_000)] | None = None
    oil_interval_months: Annotated[int, Field(gt=0, le=120)] | None = None
    notes: Notes | None = None

    _not_null = reject_null("kind", "name", "brand", "model", "year", "current_km")


class LastOilChangeRead(BaseModel):
    maintenance_id: UUID
    performed_at: datetime
    km: int
    oil_type: str | None


class OilChangeRead(BaseModel):
    """G6. `null` on the vehicle when it has no oil interval (G1)."""

    status: OilState
    primary: Criterion | None = Field(description="Criterion that is due first.")
    interval_km: int | None
    interval_months: int | None
    last: LastOilChangeRead | None
    next_km: int | None
    remaining_km: int | None
    used_km_percent: int | None = Field(description="0-100: share of the km interval used.")
    next_on: date | None
    remaining_days: int | None
    used_days_percent: int | None = Field(description="0-100: share of the time interval used.")
    estimated_km_on: date | None = Field(
        description="When the km criterion should be due at the current pace (G12)."
    )


class LastFuelingRead(BaseModel):
    id: UUID
    fueled_at: datetime
    volume_ml: int
    total_cents: int
    price_per_liter: float
    full_tank: bool


class ConsumptionPoint(BaseModel):
    fueling_id: UUID
    fueled_at: datetime
    km_l: float


class VehicleStats(BaseModel):
    last_fueling: LastFuelingRead | None
    last_consumption_km_l: float | None
    avg_consumption_km_l: float | None
    recent_consumption: list[ConsumptionPoint] = Field(description="Last 5 full-tank cycles.")
    pace_km_per_day: float | None
    month_km: int
    month_spent_cents: int
    month_fuelings_count: int
    month_maintenances_count: int


class VehicleRead(BaseModel):
    id: UUID
    kind: VehicleKind
    name: str
    brand: str
    model: str
    year: int
    fuel_type: FuelType | None
    current_km: int
    current_km_at: datetime
    oil_interval_km: int | None
    oil_interval_months: int | None
    notes: str | None
    archived_at: datetime | None
    oil_change: OilChangeRead | None
    stats: VehicleStats
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------- odometer


class OdometerReadingCreate(BaseModel):
    id: ClientId | None = None
    km: Km
    recorded_at: datetime | None = Field(default=None, description="Defaults to now.")


class OdometerReadingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    km: int
    recorded_at: datetime
    source: ReadingSource
    source_id: UUID | None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------- workshops


class WorkshopCreate(BaseModel):
    id: ClientId | None = None
    name: Name
    notes: Notes | None = None


class WorkshopUpdate(BaseModel):
    name: Name | None = None
    notes: Notes | None = None

    _not_null = reject_null("name")


class WorkshopRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str


class WorkshopRead(BaseModel):
    id: UUID
    name: str
    notes: str | None
    maintenances_count: int
    last_maintenance_at: datetime | None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------- maintenances


class MaintenanceItemIn(BaseModel):
    description: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)
    ]
    quantity: Annotated[int, Field(ge=1, le=10_000)] = 1
    unit_price_cents: Cents


class MaintenanceItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    description: str
    quantity: int
    unit_price_cents: int
    total_cents: int


_OIL_FIELDS = ("oil_type", "next_oil_change_km", "next_oil_change_on")


def _oil_fields_only_for_oil_change(model: BaseModel, kind: MaintenanceKind | None) -> None:
    if kind == MaintenanceKind.OIL_CHANGE:
        return
    for name in _OIL_FIELDS:
        if getattr(model, name) is not None:
            raise PydanticCustomError(
                "garage.oil_fields_require_oil_change",
                "Oil change fields are only allowed when kind is oil_change.",
            )


class MaintenanceCreate(BaseModel):
    id: ClientId | None = None
    kind: MaintenanceKind = MaintenanceKind.GENERAL
    performed_at: datetime
    km: Km
    workshop_id: UUID | None = None
    workshop_name: Name | None = Field(
        default=None, description="Used when `workshop_id` is absent; creates the workshop if new."
    )
    labor_cost_cents: Cents = 0
    notes: Notes | None = None
    oil_type: OilType | None = None
    next_oil_change_km: Km | None = Field(
        default=None, description="Absent: suggested from the interval. `null`: no forecast."
    )
    next_oil_change_on: date | None = Field(
        default=None, description="Absent: suggested from the interval. `null`: no forecast."
    )
    items: list[MaintenanceItemIn] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def _check_oil_fields(self) -> MaintenanceCreate:
        _oil_fields_only_for_oil_change(self, self.kind)
        return self


class MaintenanceUpdate(BaseModel):
    """Partial update. `items`, when present, replaces all the items."""

    performed_at: datetime | None = None
    km: Km | None = None
    workshop_id: UUID | None = None
    workshop_name: Name | None = None
    labor_cost_cents: Cents | None = None
    notes: Notes | None = None
    oil_type: OilType | None = None
    next_oil_change_km: Km | None = None
    next_oil_change_on: date | None = None
    items: list[MaintenanceItemIn] | None = Field(default=None, max_length=100)

    _not_null = reject_null("performed_at", "km", "labor_cost_cents", "items")


class MaintenanceRead(BaseModel):
    id: UUID
    vehicle: VehicleRef
    kind: MaintenanceKind
    performed_at: datetime
    km: int
    workshop: WorkshopRef | None
    labor_cost_cents: int
    parts_cents: int
    total_cents: int
    notes: str | None
    oil_type: str | None
    next_oil_change_km: int | None
    next_oil_change_on: date | None
    items: list[MaintenanceItemRead]
    created_at: datetime
    updated_at: datetime


class OilChangeSuggestion(BaseModel):
    next_oil_change_km: int | None
    next_oil_change_on: date | None
    interval_km: int | None
    interval_months: int | None
    pace_km_per_day: float | None
    estimated_km_on: date | None = Field(description="When the suggested km would be reached.")
    previous_oil_types: list[str] = Field(description="Oils used before, most recent first.")


# ---------------------------------------------------------------- fuelings


class FuelingCreate(BaseModel):
    id: ClientId | None = None
    fueled_at: datetime
    km: Km
    fuel_type: FuelType | None = Field(
        default=None, description="Defaults to the vehicle's usual fuel (required if it has none)."
    )
    volume_ml: Annotated[int, Field(gt=0, le=10_000_000)]
    total_cents: Annotated[int, Field(gt=0, le=10_000_000_000)]
    full_tank: bool = True
    notes: Notes | None = None


class FuelingUpdate(BaseModel):
    fueled_at: datetime | None = None
    km: Km | None = None
    fuel_type: FuelType | None = None
    volume_ml: Annotated[int, Field(gt=0, le=10_000_000)] | None = None
    total_cents: Annotated[int, Field(gt=0, le=10_000_000_000)] | None = None
    full_tank: bool | None = None
    notes: Notes | None = None

    _not_null = reject_null("fueled_at", "km", "fuel_type", "volume_ml", "total_cents", "full_tank")


class FuelingRead(BaseModel):
    id: UUID
    vehicle: VehicleRef
    fueled_at: datetime
    km: int
    fuel_type: FuelType
    volume_ml: int
    total_cents: int
    price_per_liter: float = Field(description="R$ per litre, 3 decimals (G7).")
    full_tank: bool
    consumption_km_l: float | None = Field(
        description="km/l of the full-tank cycle this fueling closes (G8), 2 decimals."
    )
    notes: str | None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------- overview and summary


class NextDue(BaseModel):
    vehicle: VehicleRef
    status: OilState
    primary: Criterion
    remaining_km: int | None
    remaining_days: int | None
    used_percent: int | None
    due_on: date | None = Field(description="Expected day (pace for km, date otherwise).")


class VehicleKm(BaseModel):
    vehicle: VehicleRef
    km: int


class GarageOverview(BaseModel):
    month: str = Field(examples=["2026-11"])
    month_fuel_cents: int
    month_fuelings_count: int
    month_km: int
    vehicles_km: list[VehicleKm]
    next_due: NextDue | None


class SummaryVehicle(BaseModel):
    vehicle: VehicleRef
    current_km: int
    oil_primary: Criterion | None
    oil_status: OilState | None
    remaining_km: int | None
    remaining_days: int | None
    used_percent: int | None


class GarageSummary(ModuleSummary):
    module: Literal["garage"] = "garage"
    vehicles_count: int
    next_due: NextDue | None
    vehicles: list[SummaryVehicle]
    month_fuel_cents: int
