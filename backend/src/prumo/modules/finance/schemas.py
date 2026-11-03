from datetime import date, datetime, time
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field, StringConstraints

from prumo.core.modules import ModuleSummary
from prumo.core.pagination import Page
from prumo.core.schemas import reject_null
from prumo.modules.finance.models import AccountKind, CategoryKind, TransactionKind
from prumo.modules.finance.rules import MAX_INSTALLMENTS, InvoiceStatus

MAX_CENTS = 100_000_000_000  # R$ 1 bilhão

Color = Literal[
    "green", "teal", "cyan", "blue", "indigo", "violet", "pink", "red", "orange", "amber", "gray"
]
Icon = Annotated[
    str,
    StringConstraints(pattern=r"^[a-z0-9-]{1,32}$"),
    Field(description="Interface icon name; clients fall back to a generic icon."),
]
AccountName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]
CategoryName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=40)]
Description = Annotated[str, StringConstraints(strip_whitespace=True, max_length=120)]
Notes = Annotated[str, StringConstraints(strip_whitespace=True, max_length=4000)]
Cents = Annotated[int, Field(ge=0, le=MAX_CENTS)]
SignedCents = Annotated[int, Field(ge=-MAX_CENTS, le=MAX_CENTS)]
Day = Annotated[int, Field(ge=1, le=31)]
Month = Annotated[str, StringConstraints(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")]


class AccountRef(BaseModel):
    id: UUID
    name: str
    kind: AccountKind
    color: str
    icon: str


class CategoryRef(BaseModel):
    id: UUID
    name: str
    kind: CategoryKind
    color: str
    icon: str


class CardRef(BaseModel):
    id: UUID
    name: str
    color: str


# ---------------------------------------------------------------- accounts


class AccountCreate(BaseModel):
    name: AccountName
    kind: AccountKind
    initial_balance_cents: SignedCents = Field(
        default=0, description="Balance when the account starts being tracked (F1)."
    )
    color: Color = "green"
    icon: Icon | None = Field(default=None, description="Defaults to an icon for the kind.")
    include_in_total: bool = True


class AccountUpdate(BaseModel):
    name: AccountName | None = None
    kind: AccountKind | None = None
    initial_balance_cents: SignedCents | None = None
    color: Color | None = None
    icon: Icon | None = None
    include_in_total: bool | None = None

    _not_null = reject_null(
        "name", "kind", "initial_balance_cents", "color", "icon", "include_in_total"
    )


class AccountRead(BaseModel):
    id: UUID
    name: str
    kind: AccountKind
    initial_balance_cents: int
    color: str
    icon: str
    include_in_total: bool
    archived_at: datetime | None
    created_at: datetime
    balance_cents: int = Field(description="F1: balance today.")
    last_transaction_on: date | None = Field(description="F14: last movement up to today.")
    month_transactions_count: int = Field(description="F14: transactions this month.")
    transactions_count: int = Field(description="All transactions; deletion needs zero (F8).")


class AccountList(BaseModel):
    items: list[AccountRead]
    total_balance_cents: int = Field(description="F2: active accounts with `include_in_total`.")


class AdjustmentCreate(BaseModel):
    balance_cents: SignedCents = Field(description="The real balance on `occurred_on`.")
    occurred_on: date | None = Field(default=None, description="Defaults to today.")
    description: Description = ""


# ---------------------------------------------------------------- categories


class CategoryCreate(BaseModel):
    kind: CategoryKind
    name: CategoryName
    color: Color = "gray"
    icon: Icon = "tag"


class CategoryUpdate(BaseModel):
    kind: CategoryKind | None = Field(default=None, description="Only while unused.")
    name: CategoryName | None = None
    color: Color | None = None
    icon: Icon | None = None

    _not_null = reject_null("kind", "name", "color", "icon")


class CategoryRead(BaseModel):
    id: UUID
    kind: CategoryKind
    name: str
    color: str
    icon: str
    archived_at: datetime | None
    transactions_count: int
    month_transactions_count: int
    month_total_cents: int


class CategoryList(BaseModel):
    month: str
    items: list[CategoryRead]


# ---------------------------------------------------------------- credit cards and invoices


class CreditCardCreate(BaseModel):
    name: AccountName
    limit_cents: Cents
    closing_day: Day
    due_day: Day
    payment_account_id: UUID | None = Field(
        default=None, description="Account suggested when paying the invoice."
    )
    color: Color = "violet"


class CreditCardUpdate(BaseModel):
    name: AccountName | None = None
    limit_cents: Cents | None = None
    closing_day: Day | None = Field(
        default=None, description="Applies to new purchases; existing ones keep their invoice."
    )
    due_day: Day | None = None
    payment_account_id: UUID | None = None
    color: Color | None = None

    _not_null = reject_null("name", "limit_cents", "closing_day", "due_day", "color")


class InvoiceRead(BaseModel):
    closing_on: date
    due_on: date
    starts_on: date = Field(description="First day of the period (previous closing).")
    ends_on: date = Field(description="Last day of the period (day before the closing).")
    amount_cents: int
    paid_cents: int
    remaining_cents: int
    status: InvoiceStatus
    transactions_count: int
    last_payment_on: date | None
    last_payment_account: AccountRef | None


class CreditCardRead(BaseModel):
    id: UUID
    name: str
    limit_cents: int
    closing_day: int
    due_day: int
    payment_account: AccountRef | None
    color: str
    archived_at: datetime | None
    created_at: datetime
    used_cents: int = Field(description="F6: purchases minus payments, future installments too.")
    available_limit_cents: int
    current_invoice: InvoiceRead = Field(description="The invoice that receives today's purchases.")
    transactions_count: int


class InvoicePaymentCreate(BaseModel):
    amount_cents: Annotated[int, Field(ge=1, le=MAX_CENTS)]
    account_id: UUID
    occurred_on: date | None = Field(default=None, description="Defaults to today.")
    occurred_time: time | None = None
    description: Description = ""


# ---------------------------------------------------------------- transactions


class TransactionCreate(BaseModel):
    kind: TransactionKind
    amount_cents: SignedCents = Field(
        description="Positive; only `adjustment` is signed. With `installments`, the total."
    )
    occurred_on: date
    occurred_time: time | None = Field(
        default=None, description="Local time, only to show and order within the day."
    )
    description: Description = Field(
        default="", description="Required for income and expenses (F16)."
    )
    notes: Notes | None = None
    account_id: UUID | None = None
    destination_account_id: UUID | None = None
    credit_card_id: UUID | None = None
    category_id: UUID | None = None
    invoice_closing_on: date | None = Field(
        default=None, description="Only for `card_payment`: the invoice being paid."
    )
    installments: Annotated[int, Field(ge=2, le=MAX_INSTALLMENTS)] | None = Field(
        default=None, description="Card expense split in installments (F10)."
    )


class TransactionUpdate(BaseModel):
    """`kind` cannot change (F16). Send `null` to clear an optional reference."""

    amount_cents: SignedCents | None = None
    occurred_on: date | None = None
    occurred_time: time | None = None
    description: Description | None = None
    notes: Notes | None = None
    account_id: UUID | None = None
    destination_account_id: UUID | None = None
    credit_card_id: UUID | None = None
    category_id: UUID | None = None
    invoice_closing_on: date | None = None

    _not_null = reject_null("amount_cents", "occurred_on", "description")


class TransactionRead(BaseModel):
    id: UUID
    kind: TransactionKind
    amount_cents: int
    occurred_on: date
    occurred_time: time | None
    description: str
    notes: str | None
    account: AccountRef | None
    destination_account: AccountRef | None
    credit_card: CardRef | None
    category: CategoryRef | None
    invoice_closing_on: date | None
    installment_group_id: UUID | None
    installment_number: int | None
    installment_count: int | None
    created_at: datetime
    updated_at: datetime


class TransactionPage(Page[TransactionRead]):
    income_cents: int = Field(description="Sum of the income of the whole filter.")
    expense_cents: int = Field(description="Sum of the expenses of the whole filter.")


class CreditCardList(BaseModel):
    items: list[CreditCardRead]


class InvoiceList(BaseModel):
    items: list[InvoiceRead]


class InvoiceDetail(InvoiceRead):
    card: CardRef
    transactions: list[TransactionRead]
    payments: list[TransactionRead]


# ---------------------------------------------------------------- overview and summary


class AccountBalance(BaseModel):
    account: AccountRef
    balance_cents: int


class MonthPoint(BaseModel):
    month: str
    income_cents: int
    expense_cents: int


class CategoryShare(BaseModel):
    category: CategoryRef
    amount_cents: int
    percent: int
    transactions_count: int


class OpenInvoice(BaseModel):
    card: CardRef
    limit_cents: int
    available_limit_cents: int
    invoice: InvoiceRead


class FinanceOverview(BaseModel):
    month: str
    until: date = Field(description="Values count transactions up to this day (F12).")
    total_balance_cents: int
    accounts_count: int
    accounts: list[AccountBalance]
    income_cents: int
    expense_cents: int
    expense_percent: int | None = Field(description="Expenses as a percentage of income.")
    result_cents: int
    series: list[MonthPoint] = Field(description="The 6 months up to `month`, oldest first.")
    expenses_by_category: list[CategoryShare]
    income_by_category: list[CategoryShare]
    open_invoices: list[OpenInvoice]


class FinanceSummary(ModuleSummary):
    module: Literal["finance"] = "finance"
    month: str
    total_balance_cents: int
    accounts: list[AccountBalance]
    income_cents: int
    expense_cents: int
    expense_percent: int | None
    expenses_by_category: list[CategoryShare]
    next_invoice: OpenInvoice | None
