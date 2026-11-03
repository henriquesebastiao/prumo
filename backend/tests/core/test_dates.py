from datetime import date

from prumo.core.dates import add_months, day_in_month, month_end


def test_add_months_clamps_to_end_of_month() -> None:
    assert add_months(date(2026, 11, 17), 3) == date(2027, 2, 17)
    assert add_months(date(2026, 1, 31), 1) == date(2026, 2, 28)
    assert add_months(date(2028, 1, 31), 1) == date(2028, 2, 29)
    assert add_months(date(2026, 12, 15), 12) == date(2027, 12, 15)
    assert add_months(date(2026, 3, 31), -1) == date(2026, 2, 28)


def test_day_in_month_and_month_end() -> None:
    assert day_in_month(2026, 2, 31) == date(2026, 2, 28)
    assert day_in_month(2026, 11, 3) == date(2026, 11, 3)
    assert month_end(date(2026, 11, 17)) == date(2026, 11, 30)
