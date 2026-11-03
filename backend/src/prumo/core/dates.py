"""Calendar helpers shared by modules."""

from calendar import monthrange
from datetime import date


def add_months(day: date, months: int) -> date:
    """`day` plus `months`, with the day limited to the end of the target month."""
    years, month_index = divmod(day.month - 1 + months, 12)
    year, month = day.year + years, month_index + 1
    return date(year, month, min(day.day, monthrange(year, month)[1]))


def day_in_month(year: int, month: int, day: int) -> date:
    """`day` of the given month, limited to the last day of that month."""
    return date(year, month, min(day, monthrange(year, month)[1]))


def month_end(day: date) -> date:
    return date(day.year, day.month, monthrange(day.year, day.month)[1])
