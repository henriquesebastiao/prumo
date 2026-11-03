"""Garage tables in the user data export (D38)."""

from sqlalchemy.orm import Session

from prumo.core.export import ModuleExport, table_rows
from prumo.modules.garage.models import (
    Fueling,
    Maintenance,
    MaintenanceItem,
    OdometerReading,
    Vehicle,
    Workshop,
)
from prumo.system.users.models import User


def build_export(session: Session, user: User) -> ModuleExport:
    return ModuleExport(
        tables={
            "vehicles": table_rows(session, Vehicle, user.id),
            "odometer_readings": table_rows(session, OdometerReading, user.id),
            "workshops": table_rows(session, Workshop, user.id),
            "maintenances": table_rows(session, Maintenance, user.id),
            "maintenance_items": table_rows(session, MaintenanceItem, user.id),
            "fuelings": table_rows(session, Fueling, user.id),
        }
    )
