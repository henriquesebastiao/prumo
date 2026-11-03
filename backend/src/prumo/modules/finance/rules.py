"""Pure calculations of the finance rules (no database). See docs/dominio.md, F4-F13."""

import re
from datetime import date
from typing import Literal

from prumo.core.dates import add_months, day_in_month

type InvoiceStatus = Literal["open", "closed", "paid", "overdue"]

MAX_INSTALLMENTS = 48


def closing_date(year: int, month: int, closing_day: int) -> date:
    """F4: the closing date of a month is `closing_day`, limited to the end of the month."""
    return day_in_month(year, month, closing_day)


def invoice_closing_for(purchase: date, closing_day: int) -> date:
    """F4: the first closing date strictly after the purchase (a purchase on the closing day goes
    to the next invoice)."""
    this_month = closing_date(purchase.year, purchase.month, closing_day)
    if purchase < this_month:
        return this_month
    following = add_months(purchase.replace(day=1), 1)
    return closing_date(following.year, following.month, closing_day)


def invoice_starts_on(closing_on: date, closing_day: int) -> date:
    """First day of the invoice period: the previous closing date (inclusive)."""
    previous = add_months(closing_on.replace(day=1), -1)
    return closing_date(previous.year, previous.month, closing_day)


def invoice_due_on(closing_on: date, due_day: int) -> date:
    """F4: the first date with `due_day` (limited to the end of the month) after the closing."""
    same_month = day_in_month(closing_on.year, closing_on.month, due_day)
    if same_month > closing_on:
        return same_month
    following = add_months(closing_on.replace(day=1), 1)
    return day_in_month(following.year, following.month, due_day)


def is_closing_date(day: date, closing_day: int) -> bool:
    return day == closing_date(day.year, day.month, closing_day)


def invoice_status(
    *, closing_on: date, due_on: date, amount_cents: int, paid_cents: int, today: date
) -> InvoiceStatus:
    """F5."""
    if today < closing_on:
        return "open"
    if paid_cents >= amount_cents:
        return "paid"
    if today > due_on:
        return "overdue"
    return "closed"


def split_installments(total_cents: int, count: int) -> list[int]:
    """F10: equal parts; the cents left over go to the first installment."""
    base, remainder = divmod(total_cents, count)
    return [base + remainder] + [base] * (count - 1)


def installment_dates(purchase: date, count: int) -> list[date]:
    """F10: installment k is on the purchase date plus k-1 months."""
    return [add_months(purchase, index) for index in range(count)]


def percent(part: int, whole: int) -> int | None:
    if whole <= 0:
        return None
    return round(part * 100 / whole)


_PLAIN = re.compile(r"^(\d{1,12})(?:[.,](\d{1,2}))?$")
_DOT_THOUSANDS = re.compile(r"^(\d{1,3}(?:\.\d{3})+)(?:,(\d{1,2}))?$")
_COMMA_THOUSANDS = re.compile(r"^(\d{1,3}(?:,\d{3})+)(?:\.(\d{1,2}))?$")


def amount_range(query: str) -> tuple[int, int] | None:
    """F13: the cents matched by a search that looks like a value, or None.

    "212,40" and "212.40" match exactly 21240; "212" matches 21200 to 21299; "1.500" and
    "1.500,00" match 150000 (dots followed by three digits are thousands separators).
    """
    text = query.strip().removeprefix("R$").strip().lstrip("+-").strip()
    for pattern, separator in (
        (_DOT_THOUSANDS, "."),
        (_COMMA_THOUSANDS, ","),
        (_PLAIN, ""),
    ):
        match = pattern.match(text)
        if match is None:
            continue
        reais = int(match.group(1).replace(separator, "") if separator else match.group(1))
        cents = match.group(2)
        if cents is None:
            if separator:
                return reais * 100, reais * 100
            return reais * 100, reais * 100 + 99
        value = reais * 100 + int(cents.ljust(2, "0"))
        return value, value
    return None
