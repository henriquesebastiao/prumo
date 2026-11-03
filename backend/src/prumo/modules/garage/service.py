"""Business rules of the garage module (docs/dominio.md, G1-G15)."""

import math
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Literal
from uuid import UUID, uuid7
from zoneinfo import ZoneInfo

from sqlalchemy import Select, delete, func, select
from sqlalchemy.orm import Session

from prumo.core.clock import utcnow
from prumo.core.dates import add_months
from prumo.core.errors import ConflictError, DomainError, NotFoundError
from prumo.core.modules import ActivityItem, UpcomingItem
from prumo.core.pagination import Page, PageParams, Sort, SortColumn, paginate
from prumo.modules.garage import rules
from prumo.modules.garage.models import (
    Fueling,
    Maintenance,
    MaintenanceItem,
    MaintenanceKind,
    OdometerReading,
    ReadingSource,
    Vehicle,
    Workshop,
)
from prumo.modules.garage.schemas import (
    ConsumptionPoint,
    FuelingCreate,
    FuelingRead,
    FuelingUpdate,
    GarageOverview,
    GarageSummary,
    LastFuelingRead,
    LastOilChangeRead,
    MaintenanceCreate,
    MaintenanceItemIn,
    MaintenanceItemRead,
    MaintenanceRead,
    MaintenanceUpdate,
    NextDue,
    OdometerReadingCreate,
    OilChangeRead,
    OilChangeSuggestion,
    SummaryVehicle,
    VehicleCreate,
    VehicleKm,
    VehicleRead,
    VehicleRef,
    VehicleStats,
    VehicleUpdate,
    WorkshopCreate,
    WorkshopRead,
    WorkshopRef,
    WorkshopUpdate,
)
from prumo.system.preferences.service import timezone_for
from prumo.system.users.models import User

ACTIVITY_PER_KIND = 10


@dataclass(frozen=True)
class Moment:
    """ "Now" in the user's time zone (S3)."""

    tz: ZoneInfo
    now: datetime

    @property
    def today(self) -> date:
        return self.now.astimezone(self.tz).date()

    @property
    def month_start(self) -> datetime:
        return datetime.combine(self.today.replace(day=1), time(), self.tz)

    @property
    def next_month_start(self) -> datetime:
        return datetime.combine(add_months(self.today.replace(day=1), 1), time(), self.tz)

    def day_of(self, moment: datetime) -> date:
        return moment.astimezone(self.tz).date()

    def start_of(self, day: date) -> datetime:
        return datetime.combine(day, time(), self.tz)


def moment_for(session: Session, user: User) -> Moment:
    return Moment(timezone_for(session, user.id), utcnow())


def _ref(vehicle: Vehicle) -> VehicleRef:
    return VehicleRef(id=vehicle.id, name=vehicle.name, kind=vehicle.kind)


# ---------------------------------------------------------------- vehicles


def get_vehicle(session: Session, user: User, vehicle_id: UUID) -> Vehicle:
    vehicle = session.scalar(
        select(Vehicle).where(Vehicle.id == vehicle_id, Vehicle.user_id == user.id)
    )
    if vehicle is None:
        raise NotFoundError()
    return vehicle


VEHICLE_SORT = {"created_at": Vehicle.created_at, "name": Vehicle.name}


def list_vehicles(
    session: Session,
    user: User,
    page: PageParams,
    *,
    archived: Literal["false", "true", "all"] = "false",
    sort: Sort | None = None,
    updated_since: datetime | None = None,
) -> Page[VehicleRead]:
    stmt = select(Vehicle).where(Vehicle.user_id == user.id)
    if archived == "false" and updated_since is None:
        stmt = stmt.where(Vehicle.archived_at.is_(None))
    elif archived == "true" and updated_since is None:
        stmt = stmt.where(Vehicle.archived_at.is_not(None))
    result = paginate(
        session,
        stmt,
        page,
        sort=sort or Sort("created_at", descending=False),
        sort_columns=VEHICLE_SORT,
        tiebreaker=(Vehicle.id,),
        updated_since=updated_since,
    )
    reads = vehicle_reads(session, user, result.items)
    return Page[VehicleRead](items=reads, total=result.total, limit=page.limit, offset=page.offset)


def create_vehicle(session: Session, user: User, data: VehicleCreate) -> Vehicle:
    now = utcnow()
    vehicle = Vehicle(
        id=data.id or uuid7(),
        user_id=user.id,
        kind=data.kind,
        name=data.name,
        brand=data.brand,
        model=data.model,
        year=data.year,
        fuel_type=data.fuel_type,
        current_km=data.current_km,
        current_km_at=now,
        oil_interval_km=data.oil_interval_km,
        oil_interval_months=data.oil_interval_months,
        notes=data.notes,
    )
    session.add(vehicle)
    session.flush()
    session.add(
        OdometerReading(
            user_id=user.id,
            vehicle_id=vehicle.id,
            km=data.current_km,
            recorded_at=now,
            source=ReadingSource.MANUAL,
        )
    )
    session.commit()
    return vehicle


def update_vehicle(session: Session, user: User, vehicle: Vehicle, data: VehicleUpdate) -> Vehicle:
    changes = data.model_dump(exclude_unset=True)
    km = changes.pop("current_km", None)
    for name, value in changes.items():
        setattr(vehicle, name, value)
    if km is not None and km != vehicle.current_km:
        _add_reading(session, user, vehicle, km, utcnow(), ReadingSource.MANUAL, None)
    session.commit()
    return vehicle


def set_archived(session: Session, vehicle: Vehicle, archived: bool) -> Vehicle:
    vehicle.archived_at = (vehicle.archived_at or utcnow()) if archived else None
    session.commit()
    return vehicle


def delete_vehicle(session: Session, vehicle: Vehicle) -> None:
    """G11: permanent; the database cascades readings, maintenances and fuelings."""
    session.delete(vehicle)
    session.commit()


# ---------------------------------------------------------------- odometer (G2, G3)


def _check_consistency(
    session: Session, vehicle_id: UUID, km: int, at: datetime, exclude_id: UUID | None = None
) -> None:
    base = select(OdometerReading).where(OdometerReading.vehicle_id == vehicle_id)
    if exclude_id is not None:
        base = base.where(OdometerReading.id != exclude_id)
    previous = session.scalar(
        base.where(OdometerReading.recorded_at < at, OdometerReading.km > km)
        .order_by(OdometerReading.km.desc())
        .limit(1)
    )
    if previous is not None:
        raise DomainError(
            "Reading is lower than a previous reading.",
            code="garage.odometer_inconsistent",
            details={
                "conflict": "previous",
                "km": previous.km,
                "recorded_at": previous.recorded_at,
            },
        )
    following = session.scalar(
        base.where(OdometerReading.recorded_at > at, OdometerReading.km < km)
        .order_by(OdometerReading.km.asc())
        .limit(1)
    )
    if following is not None:
        raise DomainError(
            "Reading is higher than a later reading.",
            code="garage.odometer_inconsistent",
            details={"conflict": "next", "km": following.km, "recorded_at": following.recorded_at},
        )


def _refresh_current_km(session: Session, vehicle: Vehicle) -> None:
    session.flush()
    latest = session.scalar(
        select(OdometerReading)
        .where(OdometerReading.vehicle_id == vehicle.id)
        .order_by(OdometerReading.recorded_at.desc(), OdometerReading.id.desc())
        .limit(1)
    )
    if latest is not None:
        vehicle.current_km = latest.km
        vehicle.current_km_at = latest.recorded_at


def _add_reading(
    session: Session,
    user: User,
    vehicle: Vehicle,
    km: int,
    at: datetime,
    source: ReadingSource,
    source_id: UUID | None,
    reading_id: UUID | None = None,
) -> OdometerReading:
    _check_consistency(session, vehicle.id, km, at)
    reading = OdometerReading(
        id=reading_id or uuid7(),
        user_id=user.id,
        vehicle_id=vehicle.id,
        km=km,
        recorded_at=at,
        source=source,
        source_id=source_id,
    )
    session.add(reading)
    _refresh_current_km(session, vehicle)
    return reading


def _source_reading(session: Session, source: ReadingSource, source_id: UUID) -> OdometerReading:
    reading = session.scalar(
        select(OdometerReading).where(
            OdometerReading.source == source, OdometerReading.source_id == source_id
        )
    )
    assert reading is not None, "every maintenance and fueling has a reading"
    return reading


def _move_reading(
    session: Session,
    vehicle: Vehicle,
    source: ReadingSource,
    source_id: UUID,
    km: int,
    at: datetime,
) -> None:
    reading = _source_reading(session, source, source_id)
    _check_consistency(session, vehicle.id, km, at, exclude_id=reading.id)
    reading.km = km
    reading.recorded_at = at
    _refresh_current_km(session, vehicle)


def _remove_reading(
    session: Session, vehicle: Vehicle, source: ReadingSource, source_id: UUID
) -> None:
    session.execute(
        delete(OdometerReading).where(
            OdometerReading.source == source, OdometerReading.source_id == source_id
        )
    )
    _refresh_current_km(session, vehicle)


def list_readings(
    session: Session,
    user: User,
    vehicle: Vehicle,
    page: PageParams,
    *,
    updated_since: datetime | None = None,
) -> Page[OdometerReading]:
    stmt = select(OdometerReading).where(
        OdometerReading.user_id == user.id, OdometerReading.vehicle_id == vehicle.id
    )
    return paginate(
        session,
        stmt,
        page,
        sort=Sort("recorded_at", descending=True),
        sort_columns={"recorded_at": OdometerReading.recorded_at},
        tiebreaker=(OdometerReading.id.desc(),),
        updated_since=updated_since,
    )


def add_manual_reading(
    session: Session, user: User, vehicle: Vehicle, data: OdometerReadingCreate
) -> OdometerReading:
    reading = _add_reading(
        session,
        user,
        vehicle,
        data.km,
        data.recorded_at or utcnow(),
        ReadingSource.MANUAL,
        None,
        reading_id=data.id,
    )
    session.commit()
    return reading


def delete_reading(session: Session, user: User, vehicle: Vehicle, reading_id: UUID) -> None:
    reading = session.scalar(
        select(OdometerReading).where(
            OdometerReading.id == reading_id,
            OdometerReading.vehicle_id == vehicle.id,
            OdometerReading.user_id == user.id,
        )
    )
    if reading is None:
        raise NotFoundError()
    if reading.source != ReadingSource.MANUAL:
        raise DomainError(
            "Only manual readings can be deleted; delete the record that created it.",
            code="garage.reading_not_manual",
            details={"source": reading.source.value},
        )
    count = session.scalar(select(func.count()).where(OdometerReading.vehicle_id == vehicle.id))
    if (count or 0) <= 1:
        raise DomainError("A vehicle keeps at least one reading.", code="garage.last_reading")
    session.delete(reading)
    _refresh_current_km(session, vehicle)
    session.commit()


# ---------------------------------------------------------------- vehicle snapshot (G6-G13)


@dataclass(frozen=True)
class Snapshot:
    vehicle: Vehicle
    oil: rules.OilStatus | None
    pace: float | None
    read: VehicleRead


def _last_oil_change(
    session: Session, vehicle: Vehicle, moment: Moment
) -> rules.LastOilChange | None:
    last = session.scalar(
        select(Maintenance)
        .where(Maintenance.vehicle_id == vehicle.id, Maintenance.kind == MaintenanceKind.OIL_CHANGE)
        .order_by(Maintenance.performed_at.desc(), Maintenance.id.desc())
        .limit(1)
    )
    if last is None:
        return None
    return rules.LastOilChange(
        maintenance_id=last.id,
        performed_at=last.performed_at,
        performed_on=moment.day_of(last.performed_at),
        km=last.km,
        oil_type=last.oil_type,
        next_km=last.next_oil_change_km,
        next_on=last.next_oil_change_on,
    )


def _oil_read(status: rules.OilStatus | None) -> OilChangeRead | None:
    if status is None:
        return None
    last = status.last
    return OilChangeRead(
        status=status.status,
        primary=status.primary,
        interval_km=status.interval_km,
        interval_months=status.interval_months,
        last=LastOilChangeRead(
            maintenance_id=last.maintenance_id,
            performed_at=last.performed_at,
            km=last.km,
            oil_type=last.oil_type,
        )
        if last
        else None,
        next_km=status.next_km,
        remaining_km=status.remaining_km,
        used_km_percent=status.used_km_percent,
        next_on=status.next_on,
        remaining_days=status.remaining_days,
        used_days_percent=status.used_days_percent,
        estimated_km_on=status.estimated_km_on,
    )


def _snapshot(session: Session, vehicle: Vehicle, moment: Moment) -> Snapshot:
    readings = [
        rules.KmPoint(reading.km, reading.recorded_at)
        for reading in session.scalars(
            select(OdometerReading).where(OdometerReading.vehicle_id == vehicle.id)
        )
    ]
    pace = rules.pace_km_per_day(readings, moment.now)
    oil = rules.oil_status(
        interval_km=vehicle.oil_interval_km,
        interval_months=vehicle.oil_interval_months,
        last=_last_oil_change(session, vehicle, moment),
        current_km=vehicle.current_km,
        today=moment.today,
        pace_km_per_day=pace,
    )

    fuelings = list(
        session.scalars(
            select(Fueling)
            .where(Fueling.vehicle_id == vehicle.id)
            .order_by(Fueling.fueled_at, Fueling.km)
        )
    )
    cycles = rules.consumption_cycles(
        [rules.FuelPoint(f.id, f.fueled_at, f.km, f.volume_ml, f.full_tank) for f in fuelings]
    )
    start, end = moment.month_start, moment.next_month_start
    month_fuelings = [f for f in fuelings if start <= f.fueled_at < end]
    month_maintenances = list(
        session.scalars(
            select(Maintenance).where(
                Maintenance.vehicle_id == vehicle.id,
                Maintenance.performed_at >= start,
                Maintenance.performed_at < end,
            )
        )
    )
    last = fuelings[-1] if fuelings else None
    stats = VehicleStats(
        last_fueling=LastFuelingRead(
            id=last.id,
            fueled_at=last.fueled_at,
            volume_ml=last.volume_ml,
            total_cents=last.total_cents,
            price_per_liter=rules.price_per_liter(last.total_cents, last.volume_ml),
            full_tank=last.full_tank,
        )
        if last
        else None,
        last_consumption_km_l=cycles[-1].km_l if cycles else None,
        avg_consumption_km_l=rules.average_consumption(cycles),
        recent_consumption=[
            ConsumptionPoint(fueling_id=c.fueling_id, fueled_at=c.fueled_at, km_l=c.km_l)
            for c in cycles[-rules.RECENT_CYCLES :]
        ],
        pace_km_per_day=pace,
        month_km=rules.month_km(readings, vehicle.current_km, start),
        month_spent_cents=sum(f.total_cents for f in month_fuelings)
        + sum(m.total_cents for m in month_maintenances),
        month_fuelings_count=len(month_fuelings),
        month_maintenances_count=len(month_maintenances),
    )
    read = VehicleRead(
        id=vehicle.id,
        kind=vehicle.kind,
        name=vehicle.name,
        brand=vehicle.brand,
        model=vehicle.model,
        year=vehicle.year,
        fuel_type=vehicle.fuel_type,
        current_km=vehicle.current_km,
        current_km_at=vehicle.current_km_at,
        oil_interval_km=vehicle.oil_interval_km,
        oil_interval_months=vehicle.oil_interval_months,
        notes=vehicle.notes,
        archived_at=vehicle.archived_at,
        oil_change=_oil_read(oil),
        stats=stats,
        created_at=vehicle.created_at,
        updated_at=vehicle.updated_at,
    )
    return Snapshot(vehicle=vehicle, oil=oil, pace=pace, read=read)


def vehicle_reads(session: Session, user: User, vehicles: Sequence[Vehicle]) -> list[VehicleRead]:
    moment = moment_for(session, user)
    return [_snapshot(session, vehicle, moment).read for vehicle in vehicles]


def vehicle_read(session: Session, user: User, vehicle: Vehicle) -> VehicleRead:
    return vehicle_reads(session, user, [vehicle])[0]


def _active_snapshots(session: Session, user: User, moment: Moment) -> list[Snapshot]:
    vehicles = session.scalars(
        select(Vehicle)
        .where(Vehicle.user_id == user.id, Vehicle.archived_at.is_(None))
        .order_by(Vehicle.created_at, Vehicle.id)
    )
    return [_snapshot(session, vehicle, moment) for vehicle in vehicles]


# ---------------------------------------------------------------- workshops (G10)


def _workshop_stats(session: Session, user: User) -> Select[Workshop, int, datetime]:
    return (
        select(Workshop, func.count(Maintenance.id), func.max(Maintenance.performed_at))
        .outerjoin(Maintenance, Maintenance.workshop_id == Workshop.id)
        .where(Workshop.user_id == user.id)
        .group_by(Workshop.id)
    )


def _workshop_read(workshop: Workshop, count: int, last: datetime | None) -> WorkshopRead:
    return WorkshopRead(
        id=workshop.id,
        name=workshop.name,
        notes=workshop.notes,
        maintenances_count=count,
        last_maintenance_at=last,
        created_at=workshop.created_at,
        updated_at=workshop.updated_at,
    )


def _escape_like(text: str) -> str:
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def list_workshops(
    session: Session,
    user: User,
    page: PageParams,
    *,
    q: str | None = None,
    updated_since: datetime | None = None,
) -> Page[WorkshopRead]:
    stmt = _workshop_stats(session, user)
    count_stmt = select(func.count()).select_from(Workshop).where(Workshop.user_id == user.id)
    if q and q.strip():
        pattern = f"%{_escape_like(q.strip())}%"
        stmt = stmt.where(Workshop.name.ilike(pattern, escape="\\"))
        count_stmt = count_stmt.where(Workshop.name.ilike(pattern, escape="\\"))
    order: tuple[SortColumn, ...] = (func.lower(Workshop.name), Workshop.id)
    if updated_since is not None:
        stmt = stmt.where(Workshop.updated_at > updated_since)
        count_stmt = count_stmt.where(Workshop.updated_at > updated_since)
        order = (Workshop.updated_at, Workshop.id)
    rows = session.execute(stmt.order_by(*order).limit(page.limit).offset(page.offset)).all()
    return Page[WorkshopRead](
        items=[_workshop_read(workshop, count, last) for workshop, count, last in rows],
        total=session.scalar(count_stmt) or 0,
        limit=page.limit,
        offset=page.offset,
    )


def get_workshop(session: Session, user: User, workshop_id: UUID) -> Workshop:
    workshop = session.scalar(
        select(Workshop).where(Workshop.id == workshop_id, Workshop.user_id == user.id)
    )
    if workshop is None:
        raise NotFoundError()
    return workshop


def workshop_read(session: Session, user: User, workshop: Workshop) -> WorkshopRead:
    row = session.execute(_workshop_stats(session, user).where(Workshop.id == workshop.id)).one()
    found, count, last = row
    return _workshop_read(found, count, last)


def _find_workshop_by_name(session: Session, user: User, name: str) -> Workshop | None:
    return session.scalar(
        select(Workshop).where(
            Workshop.user_id == user.id, func.lower(Workshop.name) == name.strip().lower()
        )
    )


def create_workshop(session: Session, user: User, data: WorkshopCreate) -> Workshop:
    if _find_workshop_by_name(session, user, data.name) is not None:
        raise ConflictError("Workshop already exists.", code="garage.workshop_exists")
    workshop = Workshop(id=data.id or uuid7(), user_id=user.id, name=data.name, notes=data.notes)
    session.add(workshop)
    session.commit()
    return workshop


def update_workshop(
    session: Session, user: User, workshop: Workshop, data: WorkshopUpdate
) -> Workshop:
    changes = data.model_dump(exclude_unset=True)
    if "name" in changes:
        existing = _find_workshop_by_name(session, user, changes["name"])
        if existing is not None and existing.id != workshop.id:
            raise ConflictError("Workshop already exists.", code="garage.workshop_exists")
    for name, value in changes.items():
        setattr(workshop, name, value)
    session.commit()
    return workshop


def delete_workshop(session: Session, workshop: Workshop) -> None:
    used = session.scalar(
        select(func.count()).select_from(Maintenance).where(Maintenance.workshop_id == workshop.id)
    )
    if used:
        raise DomainError(
            "Workshop has maintenances.",
            code="garage.workshop_in_use",
            details={"maintenances_count": used},
        )
    session.delete(workshop)
    session.commit()


def _resolve_workshop(
    session: Session, user: User, workshop_id: UUID | None, workshop_name: str | None
) -> Workshop | None:
    if workshop_id is not None:
        return get_workshop(session, user, workshop_id)
    if workshop_name:
        existing = _find_workshop_by_name(session, user, workshop_name)
        if existing is not None:
            return existing
        workshop = Workshop(user_id=user.id, name=workshop_name.strip())
        session.add(workshop)
        session.flush()
        return workshop
    return None


# ---------------------------------------------------------------- maintenances (G4, G5)


def _items(user: User, items: Sequence[MaintenanceItemIn]) -> list[MaintenanceItem]:
    return [
        MaintenanceItem(
            user_id=user.id,
            position=index,
            description=item.description,
            quantity=item.quantity,
            unit_price_cents=item.unit_price_cents,
        )
        for index, item in enumerate(items)
    ]


def get_maintenance(
    session: Session, user: User, vehicle: Vehicle, maintenance_id: UUID
) -> Maintenance:
    maintenance = session.scalar(
        select(Maintenance).where(
            Maintenance.id == maintenance_id,
            Maintenance.vehicle_id == vehicle.id,
            Maintenance.user_id == user.id,
        )
    )
    if maintenance is None:
        raise NotFoundError()
    return maintenance


MAINTENANCE_SORT = {"performed_at": Maintenance.performed_at, "km": Maintenance.km}


def list_maintenances(
    session: Session,
    user: User,
    page: PageParams,
    *,
    vehicle_id: UUID | None = None,
    kind: MaintenanceKind | None = None,
    workshop_id: UUID | None = None,
    sort: Sort | None = None,
    updated_since: datetime | None = None,
) -> Page[MaintenanceRead]:
    stmt = select(Maintenance).where(Maintenance.user_id == user.id)
    if vehicle_id is not None:
        stmt = stmt.where(Maintenance.vehicle_id == vehicle_id)
    if kind is not None:
        stmt = stmt.where(Maintenance.kind == kind)
    if workshop_id is not None:
        stmt = stmt.where(Maintenance.workshop_id == workshop_id)
    result = paginate(
        session,
        stmt,
        page,
        sort=sort or Sort("performed_at", descending=True),
        sort_columns=MAINTENANCE_SORT,
        tiebreaker=(Maintenance.id.desc(),),
        updated_since=updated_since,
    )
    return Page[MaintenanceRead](
        items=maintenance_reads(session, result.items),
        total=result.total,
        limit=page.limit,
        offset=page.offset,
    )


def create_maintenance(
    session: Session, user: User, vehicle: Vehicle, data: MaintenanceCreate
) -> Maintenance:
    workshop = _resolve_workshop(session, user, data.workshop_id, data.workshop_name)
    maintenance = Maintenance(
        id=data.id or uuid7(),
        user_id=user.id,
        vehicle_id=vehicle.id,
        kind=data.kind,
        performed_at=data.performed_at,
        km=data.km,
        workshop_id=workshop.id if workshop else None,
        labor_cost_cents=data.labor_cost_cents,
        notes=data.notes,
        oil_type=data.oil_type,
    )
    if data.kind == MaintenanceKind.OIL_CHANGE:
        moment = moment_for(session, user)
        suggested_km, suggested_on = rules.suggest_next_oil_change(
            km=data.km,
            on=moment.day_of(data.performed_at),
            interval_km=vehicle.oil_interval_km,
            interval_months=vehicle.oil_interval_months,
        )
        given = data.model_fields_set
        maintenance.next_oil_change_km = (
            data.next_oil_change_km if "next_oil_change_km" in given else suggested_km
        )
        maintenance.next_oil_change_on = (
            data.next_oil_change_on if "next_oil_change_on" in given else suggested_on
        )
    maintenance.items = _items(user, data.items)
    session.add(maintenance)
    session.flush()
    _add_reading(
        session,
        user,
        vehicle,
        data.km,
        data.performed_at,
        ReadingSource.MAINTENANCE,
        maintenance.id,
    )
    session.commit()
    return maintenance


def update_maintenance(
    session: Session,
    user: User,
    vehicle: Vehicle,
    maintenance: Maintenance,
    data: MaintenanceUpdate,
) -> Maintenance:
    changes = data.model_dump(exclude_unset=True)
    oil_fields = {"oil_type", "next_oil_change_km", "next_oil_change_on"}
    if maintenance.kind != MaintenanceKind.OIL_CHANGE and any(
        changes.get(name) is not None for name in oil_fields
    ):
        raise DomainError(
            "Oil change fields are only allowed when kind is oil_change.",
            code="garage.oil_fields_require_oil_change",
        )
    if "workshop_id" in changes or "workshop_name" in changes:
        workshop = _resolve_workshop(
            session, user, changes.get("workshop_id"), changes.get("workshop_name")
        )
        maintenance.workshop_id = workshop.id if workshop else None
        maintenance.workshop = workshop
    for name in ("labor_cost_cents", "notes", *oil_fields):
        if name in changes:
            setattr(maintenance, name, changes[name])
    if data.items is not None:
        # Items live in their own table: the maintenance is marked as changed for sync (D41).
        maintenance.updated_at = utcnow()
        maintenance.items.clear()
        session.flush()
        maintenance.items.extend(_items(user, data.items))
    moved = "km" in changes or "performed_at" in changes
    if "km" in changes:
        maintenance.km = changes["km"]
    if "performed_at" in changes:
        maintenance.performed_at = changes["performed_at"]
    if moved:
        _move_reading(
            session,
            vehicle,
            ReadingSource.MAINTENANCE,
            maintenance.id,
            maintenance.km,
            maintenance.performed_at,
        )
    session.commit()
    return maintenance


def delete_maintenance(session: Session, vehicle: Vehicle, maintenance: Maintenance) -> None:
    _remove_reading(session, vehicle, ReadingSource.MAINTENANCE, maintenance.id)
    session.delete(maintenance)
    _refresh_current_km(session, vehicle)
    session.commit()


def _vehicles_by_id(session: Session, ids: set[UUID]) -> dict[UUID, Vehicle]:
    if not ids:
        return {}
    return {v.id: v for v in session.scalars(select(Vehicle).where(Vehicle.id.in_(ids)))}


def maintenance_reads(session: Session, items: Sequence[Maintenance]) -> list[MaintenanceRead]:
    vehicles = _vehicles_by_id(session, {item.vehicle_id for item in items})
    return [
        MaintenanceRead(
            id=item.id,
            vehicle=_ref(vehicles[item.vehicle_id]),
            kind=item.kind,
            performed_at=item.performed_at,
            km=item.km,
            workshop=WorkshopRef.model_validate(item.workshop) if item.workshop else None,
            labor_cost_cents=item.labor_cost_cents,
            parts_cents=item.parts_cents,
            total_cents=item.total_cents,
            notes=item.notes,
            oil_type=item.oil_type,
            next_oil_change_km=item.next_oil_change_km,
            next_oil_change_on=item.next_oil_change_on,
            items=[MaintenanceItemRead.model_validate(part) for part in item.items],
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
        for item in items
    ]


def oil_change_suggestion(
    session: Session, user: User, vehicle: Vehicle, *, km: int | None, on: date | None
) -> OilChangeSuggestion:
    moment = moment_for(session, user)
    snapshot = _snapshot(session, vehicle, moment)
    base_km = vehicle.current_km if km is None else km
    next_km, next_on = rules.suggest_next_oil_change(
        km=base_km,
        on=on or moment.today,
        interval_km=vehicle.oil_interval_km,
        interval_months=vehicle.oil_interval_months,
    )
    estimated = None
    if next_km is not None and snapshot.pace:
        remaining = next_km - vehicle.current_km
        estimated = (
            moment.today + timedelta(days=math.ceil(remaining / snapshot.pace))
            if remaining > 0
            else moment.today
        )
    last_used = func.max(Maintenance.performed_at)
    oil_types = session.scalars(
        select(Maintenance.oil_type)
        .where(
            Maintenance.vehicle_id == vehicle.id,
            Maintenance.kind == MaintenanceKind.OIL_CHANGE,
            Maintenance.oil_type.is_not(None),
        )
        .group_by(Maintenance.oil_type)
        .order_by(last_used.desc())
        .limit(5)
    )
    return OilChangeSuggestion(
        next_oil_change_km=next_km,
        next_oil_change_on=next_on,
        interval_km=vehicle.oil_interval_km,
        interval_months=vehicle.oil_interval_months,
        pace_km_per_day=snapshot.pace,
        estimated_km_on=estimated,
        previous_oil_types=[oil for oil in oil_types if oil],
    )


# ---------------------------------------------------------------- fuelings (G7, G8)


def get_fueling(session: Session, user: User, vehicle: Vehicle, fueling_id: UUID) -> Fueling:
    fueling = session.scalar(
        select(Fueling).where(
            Fueling.id == fueling_id, Fueling.vehicle_id == vehicle.id, Fueling.user_id == user.id
        )
    )
    if fueling is None:
        raise NotFoundError()
    return fueling


FUELING_SORT = {"fueled_at": Fueling.fueled_at, "km": Fueling.km}


def list_fuelings(
    session: Session,
    user: User,
    page: PageParams,
    *,
    vehicle_id: UUID | None = None,
    from_day: date | None = None,
    to_day: date | None = None,
    sort: Sort | None = None,
    updated_since: datetime | None = None,
) -> Page[FuelingRead]:
    moment = moment_for(session, user)
    stmt = select(Fueling).where(Fueling.user_id == user.id)
    if vehicle_id is not None:
        stmt = stmt.where(Fueling.vehicle_id == vehicle_id)
    if from_day is not None:
        stmt = stmt.where(Fueling.fueled_at >= moment.start_of(from_day))
    if to_day is not None:
        stmt = stmt.where(Fueling.fueled_at < moment.start_of(to_day + timedelta(days=1)))
    result = paginate(
        session,
        stmt,
        page,
        sort=sort or Sort("fueled_at", descending=True),
        sort_columns=FUELING_SORT,
        tiebreaker=(Fueling.id.desc(),),
        updated_since=updated_since,
    )
    return Page[FuelingRead](
        items=fueling_reads(session, result.items),
        total=result.total,
        limit=page.limit,
        offset=page.offset,
    )


def create_fueling(session: Session, user: User, vehicle: Vehicle, data: FuelingCreate) -> Fueling:
    fuel_type = data.fuel_type or vehicle.fuel_type
    if fuel_type is None:
        raise DomainError(
            "Fuel type is required when the vehicle has no usual fuel.",
            code="garage.fuel_type_required",
        )
    fueling = Fueling(
        id=data.id or uuid7(),
        user_id=user.id,
        vehicle_id=vehicle.id,
        fueled_at=data.fueled_at,
        km=data.km,
        fuel_type=fuel_type,
        volume_ml=data.volume_ml,
        total_cents=data.total_cents,
        full_tank=data.full_tank,
        notes=data.notes,
    )
    session.add(fueling)
    session.flush()
    _add_reading(session, user, vehicle, data.km, data.fueled_at, ReadingSource.FUELING, fueling.id)
    session.commit()
    return fueling


def update_fueling(
    session: Session, vehicle: Vehicle, fueling: Fueling, data: FuelingUpdate
) -> Fueling:
    changes = data.model_dump(exclude_unset=True)
    for name, value in changes.items():
        setattr(fueling, name, value)
    if "km" in changes or "fueled_at" in changes:
        _move_reading(
            session, vehicle, ReadingSource.FUELING, fueling.id, fueling.km, fueling.fueled_at
        )
    session.commit()
    return fueling


def delete_fueling(session: Session, vehicle: Vehicle, fueling: Fueling) -> None:
    _remove_reading(session, vehicle, ReadingSource.FUELING, fueling.id)
    session.delete(fueling)
    _refresh_current_km(session, vehicle)
    session.commit()


def _consumption_by_fueling(session: Session, vehicle_ids: set[UUID]) -> dict[UUID, float]:
    if not vehicle_ids:
        return {}
    by_vehicle: dict[UUID, list[rules.FuelPoint]] = {}
    for fueling in session.scalars(select(Fueling).where(Fueling.vehicle_id.in_(vehicle_ids))):
        by_vehicle.setdefault(fueling.vehicle_id, []).append(
            rules.FuelPoint(
                fueling.id, fueling.fueled_at, fueling.km, fueling.volume_ml, fueling.full_tank
            )
        )
    return {
        cycle.fueling_id: cycle.km_l
        for points in by_vehicle.values()
        for cycle in rules.consumption_cycles(points)
    }


def fueling_reads(session: Session, items: Sequence[Fueling]) -> list[FuelingRead]:
    ids = {item.vehicle_id for item in items}
    vehicles = _vehicles_by_id(session, ids)
    consumption = _consumption_by_fueling(session, ids)
    return [
        FuelingRead(
            id=item.id,
            vehicle=_ref(vehicles[item.vehicle_id]),
            fueled_at=item.fueled_at,
            km=item.km,
            fuel_type=item.fuel_type,
            volume_ml=item.volume_ml,
            total_cents=item.total_cents,
            price_per_liter=rules.price_per_liter(item.total_cents, item.volume_ml),
            full_tank=item.full_tank,
            consumption_km_l=consumption.get(item.id),
            notes=item.notes,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
        for item in items
    ]


# ---------------------------------------------------------------- overview, summary, events


_STATUS_RANK = {"overdue": 0, "due_soon": 1, "ok": 2}


def _next_due(snapshots: Sequence[Snapshot]) -> NextDue | None:
    candidates = [s for s in snapshots if s.oil and s.oil.primary and s.oil.status in _STATUS_RANK]

    def key(snapshot: Snapshot) -> tuple[int, date, int]:
        oil = snapshot.oil
        assert oil is not None
        due = rules.due_on(oil)
        return (_STATUS_RANK[oil.status], due[0] if due else date.max, -(oil.used_percent or 0))

    if not candidates:
        return None
    best = min(candidates, key=key)
    oil = best.oil
    assert oil is not None
    assert oil.primary is not None
    due = rules.due_on(oil)
    return NextDue(
        vehicle=_ref(best.vehicle),
        status=oil.status,
        primary=oil.primary,
        remaining_km=oil.remaining_km,
        remaining_days=oil.remaining_days,
        used_percent=oil.used_percent,
        due_on=due[0] if due else None,
    )


def _month_fuel(session: Session, user: User, moment: Moment) -> tuple[int, int]:
    total, count = session.execute(
        select(func.coalesce(func.sum(Fueling.total_cents), 0), func.count(Fueling.id)).where(
            Fueling.user_id == user.id,
            Fueling.fueled_at >= moment.month_start,
            Fueling.fueled_at < moment.next_month_start,
        )
    ).one()
    return int(total), int(count)


def overview(session: Session, user: User) -> GarageOverview:
    moment = moment_for(session, user)
    snapshots = _active_snapshots(session, user, moment)
    fuel_cents, fuel_count = _month_fuel(session, user, moment)
    vehicles_km = [VehicleKm(vehicle=_ref(s.vehicle), km=s.read.stats.month_km) for s in snapshots]
    return GarageOverview(
        month=moment.today.strftime("%Y-%m"),
        month_fuel_cents=fuel_cents,
        month_fuelings_count=fuel_count,
        month_km=sum(item.km for item in vehicles_km),
        vehicles_km=vehicles_km,
        next_due=_next_due(snapshots),
    )


def build_summary(session: Session, user: User) -> GarageSummary:
    moment = moment_for(session, user)
    snapshots = _active_snapshots(session, user, moment)
    fuel_cents, _ = _month_fuel(session, user, moment)
    return GarageSummary(
        vehicles_count=len(snapshots),
        next_due=_next_due(snapshots),
        vehicles=[
            SummaryVehicle(
                vehicle=_ref(s.vehicle),
                current_km=s.vehicle.current_km,
                oil_primary=s.oil.primary if s.oil else None,
                oil_status=s.oil.status if s.oil else None,
                remaining_km=s.oil.remaining_km if s.oil else None,
                remaining_days=s.oil.remaining_days if s.oil else None,
                used_percent=s.oil.used_percent if s.oil else None,
            )
            for s in snapshots
        ],
        month_fuel_cents=fuel_cents,
    )


def build_upcoming(session: Session, user: User) -> list[UpcomingItem]:
    """G15: one oil change per active vehicle, on the day of its primary criterion."""
    moment = moment_for(session, user)
    items: list[UpcomingItem] = []
    for snapshot in _active_snapshots(session, user, moment):
        oil = snapshot.oil
        if oil is None or oil.status == "unknown":
            continue
        due = rules.due_on(oil)
        if due is None:
            continue
        on, basis = due
        items.append(
            UpcomingItem(
                module="garage",
                kind="garage.oil_change",
                on=on,
                subject=snapshot.vehicle.name,
                entity_id=snapshot.vehicle.id,
                data={
                    "basis": basis,
                    "status": oil.status,
                    "remaining_km": oil.remaining_km,
                    "remaining_days": oil.remaining_days,
                    "pace_km_per_day": snapshot.pace,
                    "interval_months": oil.interval_months,
                },
            )
        )
    return items


def build_activity(session: Session, user: User) -> list[ActivityItem]:
    """G15: manual km readings, fuelings and maintenances, newest first."""
    names = {
        vehicle.id: vehicle.name
        for vehicle in session.scalars(select(Vehicle).where(Vehicle.user_id == user.id))
    }
    items: list[ActivityItem] = []
    readings = session.scalars(
        select(OdometerReading)
        .where(OdometerReading.user_id == user.id, OdometerReading.source == ReadingSource.MANUAL)
        .order_by(OdometerReading.recorded_at.desc())
        .limit(ACTIVITY_PER_KIND)
    )
    items += [
        ActivityItem(
            module="garage",
            kind="garage.odometer",
            occurred_at=r.recorded_at,
            subject=names[r.vehicle_id],
            entity_id=r.vehicle_id,
            data={"km": r.km},
        )
        for r in readings
    ]
    fuelings = session.scalars(
        select(Fueling)
        .where(Fueling.user_id == user.id)
        .order_by(Fueling.fueled_at.desc())
        .limit(ACTIVITY_PER_KIND)
    )
    items += [
        ActivityItem(
            module="garage",
            kind="garage.fueling",
            occurred_at=f.fueled_at,
            subject=names[f.vehicle_id],
            entity_id=f.id,
            data={
                "vehicle_id": str(f.vehicle_id),
                "km": f.km,
                "volume_ml": f.volume_ml,
                "total_cents": f.total_cents,
            },
        )
        for f in fuelings
    ]
    maintenances = session.scalars(
        select(Maintenance)
        .where(Maintenance.user_id == user.id)
        .order_by(Maintenance.performed_at.desc())
        .limit(ACTIVITY_PER_KIND)
    )
    items += [
        ActivityItem(
            module="garage",
            kind="garage.maintenance",
            occurred_at=m.performed_at,
            subject=names[m.vehicle_id],
            entity_id=m.id,
            data={
                "vehicle_id": str(m.vehicle_id),
                "maintenance_kind": m.kind.value,
                "km": m.km,
                "total_cents": m.total_cents,
                "items_count": len(m.items),
                "workshop": m.workshop.name if m.workshop else None,
            },
        )
        for m in maintenances
    ]
    items.sort(key=lambda item: item.occurred_at, reverse=True)
    return items[:ACTIVITY_PER_KIND]
