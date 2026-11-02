"""API for the Playwright screenshots: a throwaway database seeded with the data of the design
boards, served with the clock frozen at the moment of the boards (Tue 17 Nov 2026, 14:30 in
São Paulo).

Run from backend/: `uv run python scripts/e2e_server.py` (used by frontend/playwright.config.ts).
Database: PRUMO_E2E_DATABASE_URL, default prumo_e2e on the test container (port 5433).
"""

import os
from datetime import UTC, date, datetime

import psycopg
import time_machine
import uvicorn
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

ADMIN_URL = os.environ.get(
    "PRUMO_E2E_ADMIN_URL", "postgresql://prumo:prumo@localhost:5433/prumo_test"
)
DATABASE_URL = os.environ.get(
    "PRUMO_E2E_DATABASE_URL", "postgresql+psycopg://prumo:prumo@localhost:5433/prumo_e2e"
)
PORT = int(os.environ.get("PRUMO_E2E_PORT", "8001"))
NOW = "2026-11-17T17:30:00Z"

os.environ["PRUMO_DATABASE_URL"] = DATABASE_URL
os.environ["PRUMO_COOKIE_SECURE"] = "false"


def at(value: str) -> datetime:
    return datetime.fromisoformat(value).replace(tzinfo=UTC)


def reset_database() -> None:
    with psycopg.connect(ADMIN_URL, autocommit=True) as connection:
        connection.execute("DROP DATABASE IF EXISTS prumo_e2e WITH (FORCE)")
        connection.execute("CREATE DATABASE prumo_e2e")
    config = Config("alembic.ini")
    config.attributes["configure_logger"] = False
    engine = create_engine(DATABASE_URL)
    with engine.begin() as connection:
        connection.execute(text("SELECT 1"))
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
    engine.dispose()


def seed() -> None:
    from prumo.main import bootstrap
    from prumo.modules.garage import service
    from prumo.modules.garage.models import FuelType, MaintenanceKind, VehicleKind
    from prumo.modules.garage.schemas import (
        FuelingCreate,
        MaintenanceCreate,
        MaintenanceItemIn,
        OdometerReadingCreate,
        VehicleCreate,
    )
    from prumo.system.users.service import create_user

    bootstrap()
    engine = create_engine(DATABASE_URL)
    with Session(engine, expire_on_commit=False) as session:
        with time_machine.travel(at("2025-11-19T12:00:00")):
            user = create_user(
                session,
                username="henrique",
                display_name="Henrique Sebastião",
                password="prumo-demo-01",
                is_admin=True,
            )
            cg = service.create_vehicle(
                session,
                user,
                VehicleCreate(
                    kind=VehicleKind.MOTORCYCLE,
                    name="Honda CG 160 Fan",
                    brand="Honda",
                    model="CG 160 Fan",
                    year=2023,
                    fuel_type=FuelType.GASOLINE,
                    current_km=11000,
                    oil_interval_km=1000,
                    oil_interval_months=3,
                ),
            )
        with time_machine.travel(at("2025-11-20T12:00:00")):
            strada = service.create_vehicle(
                session,
                user,
                VehicleCreate(
                    kind=VehicleKind.CAR,
                    name="Fiat Strada Freedom",
                    brand="Fiat",
                    model="Strada Freedom",
                    year=2021,
                    fuel_type=FuelType.GASOLINE,
                    current_km=46000,
                    oil_interval_km=10000,
                    oil_interval_months=12,
                ),
            )

        def maintenance(vehicle, when, km, items, labor, notes=None) -> None:  # type: ignore[no-untyped-def]
            service.create_maintenance(
                session,
                user,
                vehicle,
                MaintenanceCreate(
                    performed_at=at(when),
                    km=km,
                    workshop_name="Moto Peças Rocha",
                    labor_cost_cents=labor,
                    notes=notes,
                    items=[MaintenanceItemIn(description=d, unit_price_cents=p) for d, p in items],
                ),
            )

        def oil(vehicle, when, km, oil_type, **next_values) -> None:  # type: ignore[no-untyped-def]
            service.create_maintenance(
                session,
                user,
                vehicle,
                MaintenanceCreate(
                    kind=MaintenanceKind.OIL_CHANGE,
                    performed_at=at(when),
                    km=km,
                    oil_type=oil_type,
                    labor_cost_cents=1500,
                    items=[
                        MaintenanceItemIn(description="Óleo " + oil_type, unit_price_cents=3890)
                    ],
                    **next_values,
                ),
            )

        def fuel(vehicle, when, km, ml, cents, full=True) -> None:  # type: ignore[no-untyped-def]
            service.create_fueling(
                session,
                user,
                vehicle,
                FuelingCreate(
                    fueled_at=at(when), km=km, volume_ml=ml, total_cents=cents, full_tank=full
                ),
            )

        oil(
            strada,
            "2025-12-05T14:00:00",
            46900,
            "5W-30 sintético",
            next_oil_change_km=56900,
            next_oil_change_on=date(2026, 12, 5),
        )
        maintenance(
            cg,
            "2026-05-22T13:30:00",
            13050,
            [("Cabo de embreagem", 2800), ("Lâmpada do farol", 1890)],
            3000,
        )
        oil(cg, "2026-06-20T13:00:00", 13900, "4T 10W-30 sintético")
        maintenance(
            cg,
            "2026-07-14T13:30:00",
            14620,
            [("Pneu traseiro 90/90-18", 21900), ("Câmara de ar", 3200)],
            2500,
        )
        maintenance(
            cg,
            "2026-09-03T13:30:00",
            16180,
            [
                ("Kit relação (coroa, pinhão e corrente)", 18990),
                ("Pastilha de freio dianteira", 3450),
            ],
            6000,
            "Corrente estava no limite de esticamento. O mecânico recomendou olhar a lona do freio "
            "traseiro na próxima visita.",
        )
        oil(cg, "2026-09-12T13:00:00", 16640, "4T 20W-50 semissintético")
        fuel(cg, "2026-09-27T12:00:00", 16900, 7000, 4410)
        fuel(cg, "2026-10-07T12:00:00", 17200, 7280, 4600)
        fuel(cg, "2026-10-17T12:00:00", 17500, 7480, 4730)
        oil(cg, "2026-10-21T13:00:00", 17640, "4T 20W-50 semissintético")
        fuel(cg, "2026-10-27T12:00:00", 17800, 7520, 4770)
        fuel(cg, "2026-11-06T12:00:00", 18110, 7640, 4850)
        fuel(strada, "2026-10-28T20:00:00", 51900, 30000, 18900)
        fuel(strada, "2026-11-13T21:00:00", 52300, 28400, 18034)
        fuel(cg, "2026-11-16T21:10:00", 18400, 7300, 4636)
        with time_machine.travel(at("2026-11-15T22:20:00")):
            service.add_manual_reading(session, user, strada, OdometerReadingCreate(km=52300))
        with time_machine.travel(at("2026-11-17T10:42:00")):
            service.add_manual_reading(session, user, cg, OdometerReadingCreate(km=18420))
    engine.dispose()


def main() -> None:
    reset_database()
    seed()
    with time_machine.travel(NOW, tick=True):
        uvicorn.run(
            "prumo.main:create_app", factory=True, host="127.0.0.1", port=PORT, log_level="warning"
        )


if __name__ == "__main__":
    main()
