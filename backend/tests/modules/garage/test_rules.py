from datetime import UTC, date, datetime, timedelta
from uuid import uuid7

from prumo.modules.garage import rules
from prumo.modules.garage.rules import FuelPoint, KmPoint, LastOilChange

TODAY = date(2026, 11, 17)
NOW = datetime(2026, 11, 17, 17, 30, tzinfo=UTC)


def at(days_ago: float) -> datetime:
    return NOW - timedelta(days=days_ago)


def change(km: int, on: date, next_km: int | None, next_on: date | None) -> LastOilChange:
    return LastOilChange(
        maintenance_id=uuid7(),
        performed_at=datetime(on.year, on.month, on.day, 13, tzinfo=UTC),
        performed_on=on,
        km=km,
        oil_type="4T 20W-50",
        next_km=next_km,
        next_on=next_on,
    )


def test_suggest_next_oil_change() -> None:
    assert rules.suggest_next_oil_change(
        km=18420, on=date(2026, 11, 17), interval_km=1000, interval_months=3
    ) == (19420, date(2027, 2, 17))
    assert rules.suggest_next_oil_change(km=100, on=TODAY, interval_km=None, interval_months=6) == (
        None,
        date(2027, 5, 17),
    )


def test_no_interval_means_no_oil_status() -> None:
    assert (
        rules.oil_status(
            interval_km=None,
            interval_months=None,
            last=None,
            current_km=0,
            today=TODAY,
            pace_km_per_day=None,
        )
        is None
    )


def test_interval_without_oil_change_is_unknown() -> None:
    status = rules.oil_status(
        interval_km=1000,
        interval_months=3,
        last=None,
        current_km=0,
        today=TODAY,
        pace_km_per_day=None,
    )
    assert status is not None
    assert status.status == "unknown"
    assert status.primary is None


def test_km_primary_with_pace_estimate() -> None:
    # Design: 220 km left of 1.000, 65 days left of ~92, 29 km/day.
    status = rules.oil_status(
        interval_km=1000,
        interval_months=3,
        last=change(17640, date(2026, 10, 21), 18640, date(2027, 1, 21)),
        current_km=18420,
        today=TODAY,
        pace_km_per_day=29.0,
    )
    assert status is not None
    assert status.status == "ok"  # 22% of the km interval and 65 days left
    assert status.primary == "km"
    assert status.remaining_km == 220
    assert status.used_km_percent == 78
    assert status.remaining_days == 65
    assert status.used_days_percent == 29
    assert status.estimated_km_on == TODAY + timedelta(days=8)
    assert status.used_percent == 78
    assert rules.due_on(status) == (date(2026, 11, 25), "km_pace")


def test_ok_due_soon_and_overdue_thresholds() -> None:
    def status_for(current_km: int, next_on: date) -> str:
        result = rules.oil_status(
            interval_km=1000,
            interval_months=3,
            last=change(10000, date(2026, 9, 1), 11000, next_on),
            current_km=current_km,
            today=TODAY,
            pace_km_per_day=None,
        )
        assert result is not None
        return result.status

    far = date(2027, 3, 1)
    assert status_for(10500, far) == "ok"
    assert status_for(10900, far) == "due_soon"  # 100 km = 10% of the interval
    assert status_for(10899, TODAY + timedelta(days=15)) == "due_soon"  # 15 days
    assert status_for(11000, far) == "overdue"  # 0 km left
    assert status_for(10100, TODAY) == "overdue"  # due today


def test_primary_is_the_smallest_remaining_fraction() -> None:
    # Design (Strada): 18 days of ~365 left vs 4.600 km of 10.000 left: date wins.
    status = rules.oil_status(
        interval_km=10000,
        interval_months=12,
        last=change(46900, date(2025, 12, 5), 56900, date(2026, 12, 5)),
        current_km=52300,
        today=TODAY,
        pace_km_per_day=None,
    )
    assert status is not None
    assert status.primary == "date"
    assert status.remaining_days == 18
    assert status.used_days_percent == 95
    assert status.used_km_percent == 54
    assert rules.due_on(status) == (date(2026, 12, 5), "date")


def test_overridden_next_values_define_the_interval() -> None:
    status = rules.oil_status(
        interval_km=1000,
        interval_months=None,
        last=change(10000, date(2026, 10, 1), 12000, None),
        current_km=11000,
        today=TODAY,
        pace_km_per_day=None,
    )
    assert status is not None
    assert status.used_km_percent == 50
    assert status.status == "ok"


def test_no_forecast_on_last_change_is_unknown() -> None:
    status = rules.oil_status(
        interval_km=1000,
        interval_months=3,
        last=change(10000, date(2026, 10, 1), None, None),
        current_km=10100,
        today=TODAY,
        pace_km_per_day=10,
    )
    assert status is not None
    assert status.status == "unknown"


def test_price_per_liter_has_three_decimals() -> None:
    assert rules.price_per_liter(4636, 7300) == 6.351
    assert rules.price_per_liter(16700, 26300) == 6.35


def test_consumption_cycles_follow_the_full_tank_method() -> None:
    ids = [uuid7() for _ in range(5)]
    points = [
        FuelPoint(ids[0], at(40), 1000, 5000, full_tank=False),  # before the first full: ignored
        FuelPoint(ids[1], at(30), 1100, 6000, full_tank=True),  # first full: no consumption
        FuelPoint(ids[2], at(20), 1300, 4000, full_tank=False),  # partial: counted in next cycle
        FuelPoint(ids[3], at(10), 1500, 6000, full_tank=True),  # 400 km / 10 L
        FuelPoint(ids[4], at(1), 1800, 7500, full_tank=True),  # 300 km / 7.5 L
    ]
    cycles = rules.consumption_cycles(list(reversed(points)))  # order does not matter
    assert [(c.fueling_id, c.distance_km, c.volume_ml, c.km_l) for c in cycles] == [
        (ids[3], 400, 10000, 40.0),
        (ids[4], 300, 7500, 40.0),
    ]
    assert rules.average_consumption(cycles) == 40.0
    assert rules.average_consumption([]) is None


def test_pace_uses_the_last_30_days_from_the_previous_reading() -> None:
    points = [
        KmPoint(1000, at(90)),
        KmPoint(1300, at(40)),  # last reading before the window: starting point
        KmPoint(1600, at(20)),
        KmPoint(2500, at(0)),
    ]
    assert rules.pace_km_per_day(points, NOW) == 30.0  # 1200 km / 40 days
    assert rules.pace_km_per_day([KmPoint(1000, at(0))], NOW) is None
    assert rules.pace_km_per_day([KmPoint(1000, at(0.5)), KmPoint(1050, at(0))], NOW) is None


def test_month_km_counts_from_the_last_reading_before_the_month() -> None:
    month_start = datetime(2026, 11, 1, 3, tzinfo=UTC)
    points = [KmPoint(17000, at(30)), KmPoint(17957, at(18)), KmPoint(18420, at(0))]
    assert rules.month_km(points, 18420, month_start) == 463  # the design's "CG 160: 463"
    only_in_month = [KmPoint(18000, at(5)), KmPoint(18420, at(0))]
    assert rules.month_km(only_in_month, 18420, month_start) == 420
    assert rules.month_km([], 0, month_start) == 0
