"""Pure calculations of the garage rules (no database). See docs/dominio.md, G5-G13."""

import math
from calendar import monthrange
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Literal
from uuid import UUID

DUE_SOON_KM_FRACTION = 0.10
DUE_SOON_DAYS = 15
PACE_WINDOW = timedelta(days=30)
RECENT_CYCLES = 5

type OilState = Literal["ok", "due_soon", "overdue", "unknown"]
type Criterion = Literal["km", "date"]


def add_months(day: date, months: int) -> date:
    """`day` plus `months`, with the day limited to the end of the target month."""
    years, month_index = divmod(day.month - 1 + months, 12)
    year, month = day.year + years, month_index + 1
    return date(year, month, min(day.day, monthrange(year, month)[1]))


def suggest_next_oil_change(
    *, km: int, on: date, interval_km: int | None, interval_months: int | None
) -> tuple[int | None, date | None]:
    """G5: next oil change from the vehicle intervals."""
    next_km = km + interval_km if interval_km else None
    next_on = add_months(on, interval_months) if interval_months else None
    return next_km, next_on


# ---------------------------------------------------------------- oil status (G6, G12)


@dataclass(frozen=True)
class LastOilChange:
    maintenance_id: UUID
    performed_at: datetime
    performed_on: date
    km: int
    oil_type: str | None
    next_km: int | None
    next_on: date | None


@dataclass(frozen=True)
class OilStatus:
    status: OilState
    primary: Criterion | None
    interval_km: int | None
    interval_months: int | None
    last: LastOilChange | None = None
    next_km: int | None = None
    remaining_km: int | None = None
    used_km_percent: int | None = None
    next_on: date | None = None
    remaining_days: int | None = None
    used_days_percent: int | None = None
    estimated_km_on: date | None = None

    @property
    def used_percent(self) -> int | None:
        """Used share of the primary criterion (the ring on Início)."""
        if self.primary == "km":
            return self.used_km_percent
        if self.primary == "date":
            return self.used_days_percent
        return None


def _percent(used: float, span: float) -> int:
    return max(0, min(100, round(used / span * 100)))


def oil_status(
    *,
    interval_km: int | None,
    interval_months: int | None,
    last: LastOilChange | None,
    current_km: int,
    today: date,
    pace_km_per_day: float | None,
) -> OilStatus | None:
    if interval_km is None and interval_months is None:
        return None  # G1
    if last is None or (last.next_km is None and last.next_on is None):
        return OilStatus(
            status="unknown",
            primary=None,
            interval_km=interval_km,
            interval_months=interval_months,
            last=last,
        )

    fractions: dict[Criterion, float] = {}
    remaining_km = used_km = None
    if last.next_km is not None:
        remaining_km = last.next_km - current_km
        span = last.next_km - last.km
        if span > 0:
            used_km = _percent(current_km - last.km, span)
            fractions["km"] = remaining_km / span
    remaining_days = used_days = None
    if last.next_on is not None:
        remaining_days = (last.next_on - today).days
        span_days = (last.next_on - last.performed_on).days
        if span_days > 0:
            used_days = _percent((today - last.performed_on).days, span_days)
            fractions["date"] = remaining_days / span_days

    if fractions:
        primary: Criterion = min(fractions, key=lambda key: fractions[key])
    else:
        primary = "km" if remaining_km is not None else "date"

    overdue = (remaining_km is not None and remaining_km <= 0) or (
        remaining_days is not None and remaining_days <= 0
    )
    km_soon = (
        remaining_km is not None
        and last.next_km is not None
        and remaining_km <= DUE_SOON_KM_FRACTION * (last.next_km - last.km)
    )
    days_soon = remaining_days is not None and remaining_days <= DUE_SOON_DAYS
    status: OilState = "overdue" if overdue else "due_soon" if km_soon or days_soon else "ok"

    estimated = None
    if remaining_km is not None and pace_km_per_day and pace_km_per_day > 0:
        if remaining_km > 0:
            estimated = today + timedelta(days=math.ceil(remaining_km / pace_km_per_day))
        else:
            estimated = today

    return OilStatus(
        status=status,
        primary=primary,
        last=last,
        next_km=last.next_km,
        remaining_km=remaining_km,
        used_km_percent=used_km,
        next_on=last.next_on,
        remaining_days=remaining_days,
        used_days_percent=used_days,
        estimated_km_on=estimated,
        interval_km=interval_km,
        interval_months=interval_months,
    )


def due_on(status: OilStatus) -> tuple[date, Literal["km_pace", "date"]] | None:
    """G15: day of the primary criterion, for "Vem aí"."""
    if status.primary == "km" and status.estimated_km_on is not None:
        return status.estimated_km_on, "km_pace"
    if status.primary == "date" and status.next_on is not None:
        return status.next_on, "date"
    if status.next_on is not None:
        return status.next_on, "date"
    return None


# ---------------------------------------------------------------- consumption (G7, G8)


def price_per_liter(total_cents: int, volume_ml: int) -> float:
    """G7: R$ per litre, 3 decimals."""
    return round((total_cents / 100) / (volume_ml / 1000), 3)


@dataclass(frozen=True)
class FuelPoint:
    id: UUID
    fueled_at: datetime
    km: int
    volume_ml: int
    full_tank: bool


@dataclass(frozen=True)
class Cycle:
    fueling_id: UUID
    fueled_at: datetime
    distance_km: int
    volume_ml: int

    @property
    def km_l(self) -> float:
        return round(self.distance_km / (self.volume_ml / 1000), 2)


def consumption_cycles(points: Sequence[FuelPoint]) -> list[Cycle]:
    """G8: one cycle per full tank after a previous full tank."""
    cycles: list[Cycle] = []
    previous_full: FuelPoint | None = None
    volume = 0
    for point in sorted(points, key=lambda p: (p.fueled_at, p.km)):
        volume += point.volume_ml
        if not point.full_tank:
            continue
        if previous_full is not None and point.km > previous_full.km and volume > 0:
            cycles.append(Cycle(point.id, point.fueled_at, point.km - previous_full.km, volume))
        previous_full = point
        volume = 0
    return cycles


def average_consumption(cycles: Sequence[Cycle]) -> float | None:
    distance = sum(cycle.distance_km for cycle in cycles)
    volume = sum(cycle.volume_ml for cycle in cycles)
    return round(distance / (volume / 1000), 2) if volume else None


# ---------------------------------------------------------------- odometer (G12, G13)


@dataclass(frozen=True)
class KmPoint:
    km: int
    recorded_at: datetime


def pace_km_per_day(points: Sequence[KmPoint], now: datetime) -> float | None:
    """G12: km per day over the last 30 days (from the last reading before the window)."""
    ordered = sorted(points, key=lambda p: p.recorded_at)
    start = now - PACE_WINDOW
    before = [p for p in ordered if p.recorded_at < start]
    window = ([before[-1]] if before else []) + [p for p in ordered if p.recorded_at >= start]
    if len(window) < 2:
        return None
    first, last = window[0], window[-1]
    days = (last.recorded_at - first.recorded_at).total_seconds() / 86_400
    if days < 1:
        return None
    return round((last.km - first.km) / days, 1)


def month_km(points: Sequence[KmPoint], current_km: int, month_start: datetime) -> int:
    """G13: km since the last reading before the start of the month."""
    ordered = sorted(points, key=lambda p: p.recorded_at)
    before = [p for p in ordered if p.recorded_at < month_start]
    in_month = [p for p in ordered if p.recorded_at >= month_start]
    if before:
        base = before[-1].km
    elif in_month:
        base = in_month[0].km
    else:
        return 0
    return max(0, current_km - base)
