"""Finance rules (F4-F13): invoice dates, installments and value search."""

from datetime import date, timedelta

import pytest
from pytest_codspeed import BenchmarkFixture

from prumo.modules.finance import rules

PURCHASES = [date(2026, 1, 1) + timedelta(days=i) for i in range(365)]
QUERIES = ["212,40", "212.40", "212", "1.500", "1.500,00", "1,500.00", "R$ 89,9", "-35", "mercado"]


def test_invoice_dates_for_a_year_of_purchases(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def run() -> None:
        for purchase in PURCHASES:
            closing = rules.invoice_closing_for(purchase, 25)
            rules.invoice_starts_on(closing, 25)
            due = rules.invoice_due_on(closing, 5)
            rules.invoice_status(
                closing_on=closing,
                due_on=due,
                amount_cents=150_000,
                paid_cents=50_000,
                today=date(2026, 7, 1),
            )


@pytest.mark.parametrize("count", [12, rules.MAX_INSTALLMENTS])
def test_installments(benchmark: BenchmarkFixture, count: int) -> None:
    @benchmark
    def run() -> None:
        for purchase in PURCHASES[:60]:
            rules.split_installments(1_234_567, count)
            rules.installment_dates(purchase, count)


def test_amount_range(benchmark: BenchmarkFixture) -> None:
    @benchmark
    def run() -> None:
        for _ in range(50):
            for query in QUERIES:
                rules.amount_range(query)
