from datetime import date

from prumo.modules.finance import rules


def test_purchase_goes_to_the_first_closing_strictly_after_it() -> None:
    assert rules.invoice_closing_for(date(2026, 11, 16), 3) == date(2026, 12, 3)
    assert rules.invoice_closing_for(date(2026, 12, 2), 3) == date(2026, 12, 3)
    # On the closing day: next invoice (F4).
    assert rules.invoice_closing_for(date(2026, 12, 3), 3) == date(2027, 1, 3)
    # Closing day limited to the end of the month.
    assert rules.invoice_closing_for(date(2026, 2, 10), 31) == date(2026, 2, 28)
    assert rules.invoice_closing_for(date(2026, 2, 28), 31) == date(2026, 3, 31)


def test_invoice_period_and_due_date() -> None:
    assert rules.invoice_starts_on(date(2026, 12, 3), 3) == date(2026, 11, 3)
    assert rules.invoice_starts_on(date(2026, 3, 31), 31) == date(2026, 2, 28)
    assert rules.invoice_due_on(date(2026, 12, 3), 10) == date(2026, 12, 10)
    assert rules.invoice_due_on(date(2026, 12, 28), 5) == date(2027, 1, 5)
    assert rules.invoice_due_on(date(2026, 2, 28), 28) == date(2026, 3, 28)
    assert rules.is_closing_date(date(2026, 2, 28), 30)
    assert not rules.is_closing_date(date(2026, 2, 27), 30)


def test_invoice_status() -> None:
    def status(today: date, paid: int) -> str:
        return rules.invoice_status(
            closing_on=date(2026, 11, 3),
            due_on=date(2026, 11, 10),
            amount_cents=10000,
            paid_cents=paid,
            today=today,
        )

    assert status(date(2026, 11, 2), 10000) == "open"
    assert status(date(2026, 11, 3), 0) == "closed"
    assert status(date(2026, 11, 10), 5000) == "closed"
    assert status(date(2026, 11, 11), 5000) == "overdue"
    assert status(date(2026, 11, 11), 10000) == "paid"


def test_installments_split_and_dates() -> None:
    assert rules.split_installments(10000, 3) == [3334, 3333, 3333]
    assert rules.split_installments(9000, 3) == [3000, 3000, 3000]
    assert rules.installment_dates(date(2026, 1, 31), 3) == [
        date(2026, 1, 31),
        date(2026, 2, 28),
        date(2026, 3, 31),
    ]


def test_amount_range_reads_values_in_the_search() -> None:
    assert rules.amount_range("212,40") == (21240, 21240)
    assert rules.amount_range("212.40") == (21240, 21240)
    assert rules.amount_range("212") == (21200, 21299)
    assert rules.amount_range("2,5") == (250, 250)
    assert rules.amount_range("1.500") == (150000, 150000)
    assert rules.amount_range("1.500,00") == (150000, 150000)
    assert rules.amount_range("1,500.25") == (150025, 150025)
    assert rules.amount_range("R$ 46,36") == (4636, 4636)
    assert rules.amount_range("- 18,50") == (1850, 1850)
    assert rules.amount_range("Padaria") is None
    assert rules.amount_range("12/11") is None


def test_percent() -> None:
    assert rules.percent(2564, 5300) == 48
    assert rules.percent(1, 0) is None
