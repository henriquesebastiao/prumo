"""Garage rules (G5-G13): oil status, fuel consumption and odometer pace."""

from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from pytest_codspeed import BenchmarkFixture

from prumo.modules.garage import rules
from prumo.modules.garage.rules import FuelPoint, KmPoint, LastOilChange

TODAY = date(2026, 11, 17)
NOW = datetime(2026, 11, 17, 17, 30, tzinfo=UTC)
START = NOW - timedelta(days=730)

# Two years of fuelings every ~4 days, one partial fill out of three.
FUELINGS = [
    FuelPoint(
        id=UUID(int=i),
        fueled_at=START + timedelta(days=4 * i, hours=i % 12),
        km=10_000 + 180 * i,
        volume_ml=12_000 + (i * 137) % 2_000,
        full_tank=i % 3 != 1,
    )
    for i in range(180)
]
READINGS = [KmPoint(km=10_000 + 45 * i, recorded_at=START + timedelta(days=i)) for i in range(730)]
LAST_CHANGES = [
    LastOilChange(
        maintenance_id=UUID(int=i),
        performed_at=NOW - timedelta(days=i),
        performed_on=TODAY - timedelta(days=i),
        km=40_000 - 30 * i,
        oil_type="4T 20W-50",
        next_km=41_000 - 30 * i,
        next_on=TODAY + timedelta(days=90 - i),
    )
    for i in range(200)
]


def test_consumption(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def run() -> None:
        cycles = rules.consumption_cycles(FUELINGS)
        rules.average_consumption(cycles)
        for cycle in cycles:
            _ = cycle.km_l


def test_odometer_pace_and_month_km(benchmark: BenchmarkFixture) -> None:
    month_start = datetime(2026, 11, 1, 3, tzinfo=UTC)

    @benchmark
    def run() -> None:
        rules.pace_km_per_day(READINGS, NOW)
        rules.month_km(READINGS, 43_000, month_start)


def test_oil_status(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def run() -> None:
        for last in LAST_CHANGES:
            status = rules.oil_status(
                interval_km=1_000,
                interval_months=3,
                last=last,
                current_km=40_000,
                today=TODAY,
                pace_km_per_day=42.5,
            )
            assert status is not None
            rules.due_on(status)
            _ = status.used_percent
