from datetime import date
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from prumo.core.deps import SessionDep
from prumo.core.errors import error_responses
from prumo.core.idempotency import create_once, created_responses
from prumo.core.pagination import Page, PageDep, Sort, sort_param
from prumo.modules.garage import service
from prumo.modules.garage.models import (
    Fueling,
    Maintenance,
    MaintenanceKind,
    OdometerReading,
    Vehicle,
    Workshop,
)
from prumo.modules.garage.schemas import (
    FuelingCreate,
    FuelingRead,
    FuelingUpdate,
    GarageOverview,
    MaintenanceCreate,
    MaintenanceRead,
    MaintenanceUpdate,
    OdometerReadingCreate,
    OdometerReadingRead,
    OilChangeSuggestion,
    VehicleCreate,
    VehicleRead,
    VehicleUpdate,
    WorkshopCreate,
    WorkshopRead,
    WorkshopUpdate,
)
from prumo.system.auth.deps import CurrentUser

router = APIRouter(responses=error_responses(401, 403, 404, 422))

VehicleSort = Annotated[Sort, Depends(sort_param("created_at", "name", default="created_at"))]
MaintenanceSort = Annotated[
    Sort, Depends(sort_param("performed_at", "km", default="-performed_at"))
]
FuelingSort = Annotated[Sort, Depends(sort_param("fueled_at", "km", default="-fueled_at"))]


def _vehicle(vehicle_id: UUID, session: SessionDep, user: CurrentUser) -> Vehicle:
    return service.get_vehicle(session, user, vehicle_id)


VehicleDep = Annotated[Vehicle, Depends(_vehicle)]


# ---------------------------------------------------------------- overview and vehicles


@router.get("/overview")
def read_overview(session: SessionDep, user: CurrentUser) -> GarageOverview:
    """Month summary of all vehicles (fuel, km driven) and the next oil change due."""
    return service.overview(session, user)


@router.get("/vehicles")
def list_vehicles(
    session: SessionDep,
    user: CurrentUser,
    page: PageDep,
    sort: VehicleSort,
    archived: Literal["false", "true", "all"] = "false",
) -> Page[VehicleRead]:
    return service.list_vehicles(session, user, page, archived=archived, sort=sort)


@router.post(
    "/vehicles", status_code=status.HTTP_201_CREATED, responses=created_responses(VehicleRead)
)
def create_vehicle(
    data: VehicleCreate, session: SessionDep, user: CurrentUser, response: Response
) -> VehicleRead:
    vehicle = create_once(
        session,
        Vehicle,
        user.id,
        data.id,
        response,
        lambda: service.create_vehicle(session, user, data),
    )
    return service.vehicle_read(session, user, vehicle)


@router.get("/vehicles/{vehicle_id}")
def read_vehicle(vehicle: VehicleDep, session: SessionDep, user: CurrentUser) -> VehicleRead:
    return service.vehicle_read(session, user, vehicle)


@router.patch("/vehicles/{vehicle_id}")
def update_vehicle(
    data: VehicleUpdate, vehicle: VehicleDep, session: SessionDep, user: CurrentUser
) -> VehicleRead:
    return service.vehicle_read(session, user, service.update_vehicle(session, user, vehicle, data))


@router.delete("/vehicles/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vehicle(vehicle: VehicleDep, session: SessionDep) -> None:
    """Deletes the vehicle and all its history (G11). Prefer archiving."""
    service.delete_vehicle(session, vehicle)


@router.post("/vehicles/{vehicle_id}/archive")
def archive_vehicle(vehicle: VehicleDep, session: SessionDep, user: CurrentUser) -> VehicleRead:
    return service.vehicle_read(session, user, service.set_archived(session, vehicle, True))


@router.post("/vehicles/{vehicle_id}/unarchive")
def unarchive_vehicle(vehicle: VehicleDep, session: SessionDep, user: CurrentUser) -> VehicleRead:
    return service.vehicle_read(session, user, service.set_archived(session, vehicle, False))


# ---------------------------------------------------------------- odometer


@router.get("/vehicles/{vehicle_id}/odometer")
def list_odometer(
    vehicle: VehicleDep, session: SessionDep, user: CurrentUser, page: PageDep
) -> Page[OdometerReadingRead]:
    return service.list_readings(session, user, vehicle, page)  # type: ignore[return-value]


@router.post(
    "/vehicles/{vehicle_id}/odometer",
    status_code=status.HTTP_201_CREATED,
    responses=created_responses(OdometerReadingRead),
)
def create_odometer_reading(
    data: OdometerReadingCreate,
    vehicle: VehicleDep,
    session: SessionDep,
    user: CurrentUser,
    response: Response,
) -> OdometerReadingRead:
    reading = create_once(
        session,
        OdometerReading,
        user.id,
        data.id,
        response,
        lambda: service.add_manual_reading(session, user, vehicle, data),
    )
    return OdometerReadingRead.model_validate(reading)


@router.delete(
    "/vehicles/{vehicle_id}/odometer/{reading_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_odometer_reading(
    reading_id: UUID, vehicle: VehicleDep, session: SessionDep, user: CurrentUser
) -> None:
    service.delete_reading(session, user, vehicle, reading_id)


# ---------------------------------------------------------------- maintenances


@router.get("/maintenances")
def list_all_maintenances(
    session: SessionDep,
    user: CurrentUser,
    page: PageDep,
    sort: MaintenanceSort,
    vehicle_id: UUID | None = None,
    kind: MaintenanceKind | None = None,
    workshop_id: UUID | None = None,
) -> Page[MaintenanceRead]:
    """Maintenances of every vehicle."""
    return service.list_maintenances(
        session, user, page, vehicle_id=vehicle_id, kind=kind, workshop_id=workshop_id, sort=sort
    )


@router.get("/vehicles/{vehicle_id}/maintenances")
def list_maintenances(
    vehicle: VehicleDep,
    session: SessionDep,
    user: CurrentUser,
    page: PageDep,
    sort: MaintenanceSort,
    kind: MaintenanceKind | None = None,
) -> Page[MaintenanceRead]:
    return service.list_maintenances(
        session, user, page, vehicle_id=vehicle.id, kind=kind, sort=sort
    )


@router.post(
    "/vehicles/{vehicle_id}/maintenances",
    status_code=status.HTTP_201_CREATED,
    responses=created_responses(MaintenanceRead),
)
def create_maintenance(
    data: MaintenanceCreate,
    vehicle: VehicleDep,
    session: SessionDep,
    user: CurrentUser,
    response: Response,
) -> MaintenanceRead:
    maintenance = create_once(
        session,
        Maintenance,
        user.id,
        data.id,
        response,
        lambda: service.create_maintenance(session, user, vehicle, data),
    )
    return service.maintenance_reads(session, [maintenance])[0]


@router.get("/vehicles/{vehicle_id}/maintenances/{maintenance_id}")
def read_maintenance(
    maintenance_id: UUID, vehicle: VehicleDep, session: SessionDep, user: CurrentUser
) -> MaintenanceRead:
    maintenance = service.get_maintenance(session, user, vehicle, maintenance_id)
    return service.maintenance_reads(session, [maintenance])[0]


@router.patch("/vehicles/{vehicle_id}/maintenances/{maintenance_id}")
def update_maintenance(
    maintenance_id: UUID,
    data: MaintenanceUpdate,
    vehicle: VehicleDep,
    session: SessionDep,
    user: CurrentUser,
) -> MaintenanceRead:
    maintenance = service.get_maintenance(session, user, vehicle, maintenance_id)
    service.update_maintenance(session, user, vehicle, maintenance, data)
    return service.maintenance_reads(session, [maintenance])[0]


@router.delete(
    "/vehicles/{vehicle_id}/maintenances/{maintenance_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_maintenance(
    maintenance_id: UUID, vehicle: VehicleDep, session: SessionDep, user: CurrentUser
) -> None:
    maintenance = service.get_maintenance(session, user, vehicle, maintenance_id)
    service.delete_maintenance(session, vehicle, maintenance)


@router.get("/vehicles/{vehicle_id}/oil-change-suggestion")
def read_oil_change_suggestion(
    vehicle: VehicleDep,
    session: SessionDep,
    user: CurrentUser,
    km: Annotated[int | None, Query(ge=0)] = None,
    on: date | None = None,
) -> OilChangeSuggestion:
    """Next oil change for a km and date (defaults: current km, today), plus oils used before."""
    return service.oil_change_suggestion(session, user, vehicle, km=km, on=on)


# ---------------------------------------------------------------- fuelings


@router.get("/fuelings")
def list_all_fuelings(
    session: SessionDep,
    user: CurrentUser,
    page: PageDep,
    sort: FuelingSort,
    vehicle_id: UUID | None = None,
    from_: Annotated[date | None, Query(alias="from")] = None,
    to: date | None = None,
) -> Page[FuelingRead]:
    """Fuelings of every vehicle. `from` and `to` are days in the user's time zone."""
    return service.list_fuelings(
        session, user, page, vehicle_id=vehicle_id, from_day=from_, to_day=to, sort=sort
    )


@router.get("/vehicles/{vehicle_id}/fuelings")
def list_fuelings(
    vehicle: VehicleDep, session: SessionDep, user: CurrentUser, page: PageDep, sort: FuelingSort
) -> Page[FuelingRead]:
    return service.list_fuelings(session, user, page, vehicle_id=vehicle.id, sort=sort)


@router.post(
    "/vehicles/{vehicle_id}/fuelings",
    status_code=status.HTTP_201_CREATED,
    responses=created_responses(FuelingRead),
)
def create_fueling(
    data: FuelingCreate,
    vehicle: VehicleDep,
    session: SessionDep,
    user: CurrentUser,
    response: Response,
) -> FuelingRead:
    fueling = create_once(
        session,
        Fueling,
        user.id,
        data.id,
        response,
        lambda: service.create_fueling(session, user, vehicle, data),
    )
    return service.fueling_reads(session, [fueling])[0]


@router.get("/vehicles/{vehicle_id}/fuelings/{fueling_id}")
def read_fueling(
    fueling_id: UUID, vehicle: VehicleDep, session: SessionDep, user: CurrentUser
) -> FuelingRead:
    fueling = service.get_fueling(session, user, vehicle, fueling_id)
    return service.fueling_reads(session, [fueling])[0]


@router.patch("/vehicles/{vehicle_id}/fuelings/{fueling_id}")
def update_fueling(
    fueling_id: UUID,
    data: FuelingUpdate,
    vehicle: VehicleDep,
    session: SessionDep,
    user: CurrentUser,
) -> FuelingRead:
    fueling = service.get_fueling(session, user, vehicle, fueling_id)
    service.update_fueling(session, vehicle, fueling, data)
    return service.fueling_reads(session, [fueling])[0]


@router.delete(
    "/vehicles/{vehicle_id}/fuelings/{fueling_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_fueling(
    fueling_id: UUID, vehicle: VehicleDep, session: SessionDep, user: CurrentUser
) -> None:
    fueling = service.get_fueling(session, user, vehicle, fueling_id)
    service.delete_fueling(session, vehicle, fueling)


# ---------------------------------------------------------------- workshops


@router.get("/workshops")
def list_workshops(
    session: SessionDep, user: CurrentUser, page: PageDep, q: str | None = None
) -> Page[WorkshopRead]:
    """Workshops with usage statistics, filtered by name (`q`)."""
    return service.list_workshops(session, user, page, q=q)


@router.post(
    "/workshops", status_code=status.HTTP_201_CREATED, responses=created_responses(WorkshopRead)
)
def create_workshop(
    data: WorkshopCreate, session: SessionDep, user: CurrentUser, response: Response
) -> WorkshopRead:
    workshop = create_once(
        session,
        Workshop,
        user.id,
        data.id,
        response,
        lambda: service.create_workshop(session, user, data),
    )
    return service.workshop_read(session, user, workshop)


@router.patch("/workshops/{workshop_id}", responses=error_responses(409))
def update_workshop(
    workshop_id: UUID, data: WorkshopUpdate, session: SessionDep, user: CurrentUser
) -> WorkshopRead:
    workshop = service.get_workshop(session, user, workshop_id)
    return service.workshop_read(
        session, user, service.update_workshop(session, user, workshop, data)
    )


@router.delete("/workshops/{workshop_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workshop(workshop_id: UUID, session: SessionDep, user: CurrentUser) -> None:
    service.delete_workshop(session, service.get_workshop(session, user, workshop_id))
