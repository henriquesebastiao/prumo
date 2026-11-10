"""Business rules of the finance module (docs/dominio.md, F1-F16)."""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Literal
from uuid import UUID, uuid7
from zoneinfo import ZoneInfo

from sqlalchemy import ColumnElement, case, delete, func, or_, select, union_all
from sqlalchemy.orm import Session

from prumo.core.clock import utcnow
from prumo.core.dates import add_months, month_end
from prumo.core.errors import ConflictError, DomainError, NotFoundError
from prumo.core.modules import ActivityItem, UpcomingItem
from prumo.core.pagination import PageParams, Sort, paginate
from prumo.modules.finance import rules
from prumo.modules.finance.models import (
    Account,
    AccountKind,
    Category,
    CategoryKind,
    CreditCard,
    Transaction,
    TransactionKind,
)
from prumo.modules.finance.schemas import (
    AccountBalance,
    AccountCreate,
    AccountList,
    AccountRead,
    AccountRef,
    AccountUpdate,
    AdjustmentCreate,
    CardRef,
    CategoryCreate,
    CategoryList,
    CategoryRead,
    CategoryRef,
    CategoryShare,
    CategoryUpdate,
    CreditCardCreate,
    CreditCardRead,
    CreditCardUpdate,
    FinanceOverview,
    FinanceSummary,
    InvoiceDetail,
    InvoicePaymentCreate,
    InvoiceRead,
    MonthPoint,
    OpenInvoice,
    TransactionCreate,
    TransactionPage,
    TransactionRead,
    TransactionUpdate,
)
from prumo.system.preferences.service import timezone_for
from prumo.system.users.models import User

type Archived = Literal["false", "true", "all"]

INCOME = TransactionKind.INCOME
EXPENSE = TransactionKind.EXPENSE
TRANSFER = TransactionKind.TRANSFER
CARD_PAYMENT = TransactionKind.CARD_PAYMENT
ADJUSTMENT = TransactionKind.ADJUSTMENT

ACTIVITY_LIMIT = 10
SERIES_MONTHS = 6

# F7. Names are user data (editable), created in the default locale.
DEFAULT_CATEGORIES: tuple[tuple[CategoryKind, str, str, str], ...] = (
    (CategoryKind.EXPENSE, "Alimentação", "orange", "utensils"),
    (CategoryKind.EXPENSE, "Moradia", "blue", "house"),
    (CategoryKind.EXPENSE, "Transporte", "indigo", "bus"),
    (CategoryKind.EXPENSE, "Combustível", "gray", "fuel"),
    (CategoryKind.EXPENSE, "Saúde", "red", "heart-pulse"),
    (CategoryKind.EXPENSE, "Educação", "violet", "graduation-cap"),
    (CategoryKind.EXPENSE, "Lazer", "pink", "ticket"),
    (CategoryKind.EXPENSE, "Compras", "amber", "shopping-bag"),
    (CategoryKind.EXPENSE, "Assinaturas", "cyan", "repeat"),
    (CategoryKind.EXPENSE, "Outros", "gray", "tag"),
    (CategoryKind.INCOME, "Salário", "green", "briefcase"),
    (CategoryKind.INCOME, "Freelance", "teal", "code-xml"),
    (CategoryKind.INCOME, "Rendimentos", "cyan", "trending-up"),
    (CategoryKind.INCOME, "Outros", "gray", "tag"),
)

ACCOUNT_ICONS = {
    AccountKind.CHECKING: "landmark",
    AccountKind.SAVINGS: "vault",
    AccountKind.CASH: "wallet",
    AccountKind.INVESTMENT: "trending-up",
    AccountKind.OTHER: "wallet",
}


@dataclass(frozen=True)
class Moment:
    """ "Now" in the user's time zone (S3)."""

    tz: ZoneInfo
    now: datetime

    @property
    def today(self) -> date:
        return self.now.astimezone(self.tz).date()

    @property
    def month_start(self) -> date:
        return self.today.replace(day=1)


def moment_for(session: Session, user: User) -> Moment:
    return Moment(timezone_for(session, user.id), utcnow())


def _archived_filter[M: (Account, Category, CreditCard)](
    model: type[M], archived: Archived
) -> ColumnElement[bool] | None:
    if archived == "false":
        return model.archived_at.is_(None)
    if archived == "true":
        return model.archived_at.is_not(None)
    return None


def _set_archived[M: (Account, Category, CreditCard)](
    session: Session, item: M, archived: bool
) -> M:
    if archived and item.archived_at is None:
        item.archived_at = utcnow()
    elif not archived:
        item.archived_at = None
    session.commit()
    return item


# ---------------------------------------------------------------- references


@dataclass(frozen=True)
class Lookup:
    """Every account, category and card of the user (small sets), to build references."""

    accounts: dict[UUID, Account]
    categories: dict[UUID, Category]
    cards: dict[UUID, CreditCard]

    def account(self, account_id: UUID | None) -> AccountRef | None:
        return account_ref(self.accounts[account_id]) if account_id else None

    def category(self, category_id: UUID | None) -> CategoryRef | None:
        return category_ref(self.categories[category_id]) if category_id else None

    def card(self, card_id: UUID | None) -> CardRef | None:
        return card_ref(self.cards[card_id]) if card_id else None


def lookup_for(session: Session, user: User) -> Lookup:
    def load[M: (Account, Category, CreditCard)](model: type[M]) -> dict[UUID, M]:
        items = session.scalars(
            select(model).where(model.user_id == user.id).order_by(model.created_at, model.id)
        )
        return {item.id: item for item in items}

    return Lookup(load(Account), load(Category), load(CreditCard))


def account_ref(account: Account) -> AccountRef:
    return AccountRef(
        id=account.id, name=account.name, kind=account.kind, color=account.color, icon=account.icon
    )


def category_ref(category: Category) -> CategoryRef:
    return CategoryRef(
        id=category.id,
        name=category.name,
        kind=category.kind,
        color=category.color,
        icon=category.icon,
    )


def card_ref(card: CreditCard) -> CardRef:
    return CardRef(id=card.id, name=card.name, color=card.color)


# ---------------------------------------------------------------- accounts (F1, F2, F11, F14)

# Effect of a transaction on its `account_id` (F1); transfers also add to the destination.
_ACCOUNT_EFFECT = case(
    (Transaction.kind.in_([INCOME, ADJUSTMENT]), Transaction.amount_cents),
    else_=-Transaction.amount_cents,
)


def get_account(session: Session, user: User, account_id: UUID) -> Account:
    account = session.scalar(
        select(Account).where(Account.id == account_id, Account.user_id == user.id)
    )
    if account is None:
        raise NotFoundError(details={"resource": "account"})
    return account


def _movements(session: Session, user: User, as_of: date) -> dict[UUID, int]:
    """F1: the sum of the transactions of each account up to `as_of` (no initial balance)."""
    totals: dict[UUID, int] = {}
    outgoing = session.execute(
        select(Transaction.account_id, func.sum(_ACCOUNT_EFFECT))
        .where(
            Transaction.user_id == user.id,
            Transaction.account_id.is_not(None),
            Transaction.occurred_on <= as_of,
        )
        .group_by(Transaction.account_id)
    )
    incoming = session.execute(
        select(Transaction.destination_account_id, func.sum(Transaction.amount_cents))
        .where(
            Transaction.user_id == user.id,
            Transaction.kind == TRANSFER,
            Transaction.destination_account_id.is_not(None),
            Transaction.occurred_on <= as_of,
        )
        .group_by(Transaction.destination_account_id)
    )
    for account_id, total in [*outgoing, *incoming]:
        if account_id is not None:
            totals[account_id] = totals.get(account_id, 0) + int(total or 0)
    return totals


def balances(
    session: Session, user: User, accounts: Iterable[Account], as_of: date
) -> dict[UUID, int]:
    movements = _movements(session, user, as_of)
    return {a.id: a.initial_balance_cents + movements.get(a.id, 0) for a in accounts}


@dataclass(frozen=True)
class AccountStats:
    last_on: date | None = None
    month_count: int = 0
    count: int = 0


def _account_stats(session: Session, user: User, moment: Moment) -> dict[UUID, AccountStats]:
    sides = union_all(
        select(
            Transaction.account_id.label("account_id"), Transaction.occurred_on.label("day")
        ).where(Transaction.user_id == user.id, Transaction.account_id.is_not(None)),
        select(
            Transaction.destination_account_id.label("account_id"),
            Transaction.occurred_on.label("day"),
        ).where(Transaction.user_id == user.id, Transaction.destination_account_id.is_not(None)),
    ).subquery()
    today = moment.today
    rows = session.execute(
        select(
            sides.c.account_id,
            func.max(case((sides.c.day <= today, sides.c.day))),
            func.count().filter(sides.c.day.between(moment.month_start, today)),
            func.count(),
        ).group_by(sides.c.account_id)
    )
    return {
        account_id: AccountStats(last_on, month_count, count)
        for account_id, last_on, month_count, count in rows
    }


def account_reads(
    session: Session, user: User, accounts: Sequence[Account], moment: Moment | None = None
) -> list[AccountRead]:
    moment = moment or moment_for(session, user)
    balance = balances(session, user, accounts, moment.today)
    stats = _account_stats(session, user, moment)
    return [
        AccountRead(
            id=a.id,
            name=a.name,
            kind=a.kind,
            initial_balance_cents=a.initial_balance_cents,
            color=a.color,
            icon=a.icon,
            include_in_total=a.include_in_total,
            archived_at=a.archived_at,
            created_at=a.created_at,
            balance_cents=balance[a.id],
            last_transaction_on=stats.get(a.id, AccountStats()).last_on,
            month_transactions_count=stats.get(a.id, AccountStats()).month_count,
            transactions_count=stats.get(a.id, AccountStats()).count,
        )
        for a in accounts
    ]


def account_read(session: Session, user: User, account: Account) -> AccountRead:
    return account_reads(session, user, [account])[0]


def _counts_in_total(account: Account) -> bool:
    return account.archived_at is None and account.include_in_total


def list_accounts(session: Session, user: User, *, archived: Archived = "false") -> AccountList:
    """F2: `total_balance_cents` always covers the active accounts, whatever the filter."""
    accounts = list(lookup_for(session, user).accounts.values())
    reads = {read.id: read for read in account_reads(session, user, accounts)}
    total = sum(reads[a.id].balance_cents for a in accounts if _counts_in_total(a))
    shown = [
        reads[a.id]
        for a in accounts
        if archived == "all" or (a.archived_at is None) == (archived == "false")
    ]
    return AccountList(items=shown, total_balance_cents=total)


def create_account(session: Session, user: User, data: AccountCreate) -> Account:
    account = Account(
        id=data.id or uuid7(),
        user_id=user.id,
        name=data.name,
        kind=data.kind,
        initial_balance_cents=data.initial_balance_cents,
        color=data.color,
        icon=data.icon or ACCOUNT_ICONS[data.kind],
        include_in_total=data.include_in_total,
    )
    session.add(account)
    session.commit()
    return account


def update_account(session: Session, account: Account, data: AccountUpdate) -> Account:
    for name, value in data.model_dump(exclude_unset=True).items():
        setattr(account, name, value)
    session.commit()
    return account


def set_account_archived(session: Session, account: Account, archived: bool) -> Account:
    return _set_archived(session, account, archived)


def delete_account(session: Session, account: Account) -> None:
    """F8: only accounts without transactions can be deleted."""
    used = session.scalar(
        select(func.count())
        .select_from(Transaction)
        .where(
            or_(
                Transaction.account_id == account.id,
                Transaction.destination_account_id == account.id,
            )
        )
    )
    if used:
        raise DomainError(
            "Account has transactions; archive it instead.",
            code="finance.account_in_use",
            details={"transactions_count": used},
        )
    session.delete(account)
    session.commit()


def adjust_balance(
    session: Session, user: User, account: Account, data: AdjustmentCreate
) -> Transaction:
    """F11: an `adjustment` with the difference between the real and the computed balance."""
    on = data.occurred_on or moment_for(session, user).today
    current = balances(session, user, [account], on)[account.id]
    difference = data.balance_cents - current
    if difference == 0:
        raise DomainError("The balance is already correct.", code="finance.balance_unchanged")
    transaction = Transaction(
        id=data.id or uuid7(),
        user_id=user.id,
        kind=ADJUSTMENT,
        amount_cents=difference,
        occurred_on=on,
        description=data.description,
        account_id=account.id,
    )
    session.add(transaction)
    session.commit()
    return transaction


# ---------------------------------------------------------------- categories (F7, F8)


def create_default_categories(session: Session, user: User) -> None:
    """F7: `on_user_created` hook (the module migration does the same for existing users)."""
    session.add_all(
        Category(user_id=user.id, kind=kind, name=name, color=color, icon=icon)
        for kind, name, color, icon in DEFAULT_CATEGORIES
    )
    session.flush()


def get_category(session: Session, user: User, category_id: UUID) -> Category:
    category = session.scalar(
        select(Category).where(Category.id == category_id, Category.user_id == user.id)
    )
    if category is None:
        raise NotFoundError(details={"resource": "category"})
    return category


def _until(first: date, moment: Moment) -> date:
    """F12: month values count transactions up to today in the current month, or up to the end
    of any other month."""
    return moment.today if first == moment.month_start else month_end(first)


def parse_month(month: str | None, moment: Moment) -> date:
    if month is None:
        return moment.month_start
    year, number = month.split("-")
    return date(int(year), int(number), 1)


@dataclass(frozen=True)
class CategoryStats:
    count: int = 0
    month_count: int = 0
    month_total: int = 0


def _category_stats(
    session: Session, user: User, start: date, until: date
) -> dict[UUID, CategoryStats]:
    in_month = Transaction.occurred_on.between(start, until)
    rows = session.execute(
        select(
            Transaction.category_id,
            func.count(),
            func.count().filter(in_month),
            func.coalesce(func.sum(Transaction.amount_cents).filter(in_month), 0),
        )
        .where(Transaction.user_id == user.id, Transaction.category_id.is_not(None))
        .group_by(Transaction.category_id)
    )
    return {
        category_id: CategoryStats(count, month_count, int(total))
        for category_id, count, month_count, total in rows
        if category_id is not None
    }


def _category_read(category: Category, stats: CategoryStats) -> CategoryRead:
    return CategoryRead(
        id=category.id,
        kind=category.kind,
        name=category.name,
        color=category.color,
        icon=category.icon,
        archived_at=category.archived_at,
        transactions_count=stats.count,
        month_transactions_count=stats.month_count,
        month_total_cents=stats.month_total,
    )


def list_categories(
    session: Session,
    user: User,
    *,
    kind: CategoryKind | None = None,
    archived: Archived = "false",
    month: str | None = None,
) -> CategoryList:
    moment = moment_for(session, user)
    first = parse_month(month, moment)
    stats = _category_stats(session, user, first, _until(first, moment))
    stmt = select(Category).where(Category.user_id == user.id)
    if kind is not None:
        stmt = stmt.where(Category.kind == kind)
    if (condition := _archived_filter(Category, archived)) is not None:
        stmt = stmt.where(condition)
    categories = session.scalars(stmt.order_by(Category.created_at, Category.id))
    return CategoryList(
        month=first.strftime("%Y-%m"),
        items=[_category_read(c, stats.get(c.id, CategoryStats())) for c in categories],
    )


def category_read(session: Session, user: User, category: Category) -> CategoryRead:
    moment = moment_for(session, user)
    stats = _category_stats(session, user, moment.month_start, moment.today)
    return _category_read(category, stats.get(category.id, CategoryStats()))


def _category_used(session: Session, category: Category) -> int:
    return (
        session.scalar(
            select(func.count())
            .select_from(Transaction)
            .where(Transaction.category_id == category.id)
        )
        or 0
    )


def _check_category_name(
    session: Session, user: User, kind: CategoryKind, name: str, exclude: UUID | None = None
) -> None:
    stmt = select(Category.id).where(
        Category.user_id == user.id,
        Category.kind == kind,
        func.lower(Category.name) == name.lower(),
    )
    if exclude is not None:
        stmt = stmt.where(Category.id != exclude)
    if session.scalar(stmt) is not None:
        raise ConflictError("Category already exists.", code="finance.category_exists")


def create_category(session: Session, user: User, data: CategoryCreate) -> Category:
    _check_category_name(session, user, data.kind, data.name)
    category = Category(
        id=data.id or uuid7(),
        user_id=user.id,
        kind=data.kind,
        name=data.name,
        color=data.color,
        icon=data.icon,
    )
    session.add(category)
    session.commit()
    return category


def update_category(
    session: Session, user: User, category: Category, data: CategoryUpdate
) -> Category:
    values = data.model_dump(exclude_unset=True)
    kind = values.get("kind", category.kind)
    if kind != category.kind and (used := _category_used(session, category)):
        raise DomainError(
            "Category has transactions; its kind cannot change.",
            code="finance.category_in_use",
            details={"transactions_count": used},
        )
    if "name" in values or "kind" in values:
        _check_category_name(
            session, user, kind, values.get("name", category.name), exclude=category.id
        )
    for name, value in values.items():
        setattr(category, name, value)
    session.commit()
    return category


def set_category_archived(session: Session, category: Category, archived: bool) -> Category:
    return _set_archived(session, category, archived)


def delete_category(session: Session, category: Category) -> None:
    """F8: only unused categories can be deleted."""
    if used := _category_used(session, category):
        raise DomainError(
            "Category has transactions; archive it instead.",
            code="finance.category_in_use",
            details={"transactions_count": used},
        )
    session.delete(category)
    session.commit()


# ---------------------------------------------------------------- credit cards (F4-F6)


def get_card(session: Session, user: User, card_id: UUID) -> CreditCard:
    card = session.scalar(
        select(CreditCard).where(CreditCard.id == card_id, CreditCard.user_id == user.id)
    )
    if card is None:
        raise NotFoundError(details={"resource": "credit_card"})
    return card


@dataclass
class InvoiceTotals:
    amount: int = 0
    paid: int = 0
    count: int = 0
    last_payment_on: date | None = None
    last_payment_account_id: UUID | None = None


type InvoiceKey = tuple[UUID, date]


def _invoice_totals(
    session: Session, user: User, card_ids: Iterable[UUID]
) -> dict[InvoiceKey, InvoiceTotals]:
    """F5: amount, payments and purchases of every invoice of the cards."""
    ids = list(card_ids)
    totals: dict[InvoiceKey, InvoiceTotals] = {}
    if not ids:
        return totals
    rows = session.execute(
        select(
            Transaction.credit_card_id,
            Transaction.invoice_closing_on,
            Transaction.kind,
            func.sum(Transaction.amount_cents),
            func.count(),
        )
        .where(
            Transaction.user_id == user.id,
            Transaction.credit_card_id.in_(ids),
            Transaction.invoice_closing_on.is_not(None),
        )
        .group_by(Transaction.credit_card_id, Transaction.invoice_closing_on, Transaction.kind)
    )
    for card_id, closing_on, kind, total, count in rows:
        if card_id is None or closing_on is None:
            continue
        entry = totals.setdefault((card_id, closing_on), InvoiceTotals())
        if kind == EXPENSE:
            entry.amount += int(total)
            entry.count += count
        elif kind == CARD_PAYMENT:
            entry.paid += int(total)
    payments = session.execute(
        select(
            Transaction.credit_card_id,
            Transaction.invoice_closing_on,
            Transaction.occurred_on,
            Transaction.account_id,
        )
        .where(
            Transaction.user_id == user.id,
            Transaction.credit_card_id.in_(ids),
            Transaction.kind == CARD_PAYMENT,
        )
        .order_by(
            Transaction.occurred_on,
            Transaction.occurred_time.nulls_first(),
            Transaction.created_at,
        )
    )
    for card_id, closing_on, occurred_on, account_id in payments:
        if card_id is None or closing_on is None:
            continue
        entry = totals.setdefault((card_id, closing_on), InvoiceTotals())
        entry.last_payment_on = occurred_on
        entry.last_payment_account_id = account_id
    return totals


def _invoice_read(
    card: CreditCard, closing_on: date, totals: InvoiceTotals, today: date, lookup: Lookup
) -> InvoiceRead:
    due_on = rules.invoice_due_on(closing_on, card.due_day)
    return InvoiceRead(
        closing_on=closing_on,
        due_on=due_on,
        starts_on=rules.invoice_starts_on(closing_on, card.closing_day),
        ends_on=closing_on - timedelta(days=1),
        amount_cents=totals.amount,
        paid_cents=totals.paid,
        remaining_cents=max(totals.amount - totals.paid, 0),
        status=rules.invoice_status(
            closing_on=closing_on,
            due_on=due_on,
            amount_cents=totals.amount,
            paid_cents=totals.paid,
            today=today,
        ),
        transactions_count=totals.count,
        last_payment_on=totals.last_payment_on,
        last_payment_account=lookup.account(totals.last_payment_account_id),
    )


def _current_closing(card: CreditCard, today: date) -> date:
    """The invoice that receives a purchase made today."""
    return rules.invoice_closing_for(today, card.closing_day)


def _used(totals: dict[InvoiceKey, InvoiceTotals], card: CreditCard) -> int:
    """F6: purchases minus payments, every invoice (future installments too)."""
    return sum(t.amount - t.paid for (card_id, _), t in totals.items() if card_id == card.id)


def card_reads(
    session: Session, user: User, cards: Sequence[CreditCard], lookup: Lookup | None = None
) -> list[CreditCardRead]:
    lookup = lookup or lookup_for(session, user)
    today = moment_for(session, user).today
    totals = _invoice_totals(session, user, [card.id for card in cards])
    counts: dict[UUID | None, int] = dict(
        session.execute(
            select(Transaction.credit_card_id, func.count())
            .where(Transaction.user_id == user.id, Transaction.credit_card_id.is_not(None))
            .group_by(Transaction.credit_card_id)
        ).all()
    )
    reads = []
    for card in cards:
        used = _used(totals, card)
        closing = _current_closing(card, today)
        reads.append(
            CreditCardRead(
                id=card.id,
                name=card.name,
                limit_cents=card.limit_cents,
                closing_day=card.closing_day,
                due_day=card.due_day,
                payment_account=lookup.account(card.payment_account_id),
                color=card.color,
                archived_at=card.archived_at,
                created_at=card.created_at,
                used_cents=used,
                available_limit_cents=card.limit_cents - used,
                current_invoice=_invoice_read(
                    card, closing, totals.get((card.id, closing), InvoiceTotals()), today, lookup
                ),
                transactions_count=counts.get(card.id, 0),
            )
        )
    return reads


def card_read(session: Session, user: User, card: CreditCard) -> CreditCardRead:
    return card_reads(session, user, [card])[0]


def list_cards(
    session: Session, user: User, *, archived: Archived = "false"
) -> list[CreditCardRead]:
    stmt = select(CreditCard).where(CreditCard.user_id == user.id)
    if (condition := _archived_filter(CreditCard, archived)) is not None:
        stmt = stmt.where(condition)
    cards = list(session.scalars(stmt.order_by(CreditCard.created_at, CreditCard.id)))
    return card_reads(session, user, cards)


def create_card(session: Session, user: User, data: CreditCardCreate) -> CreditCard:
    if data.payment_account_id is not None:
        get_account(session, user, data.payment_account_id)
    card = CreditCard(id=data.id or uuid7(), user_id=user.id, **data.model_dump(exclude={"id"}))
    session.add(card)
    session.commit()
    return card


def update_card(
    session: Session, user: User, card: CreditCard, data: CreditCardUpdate
) -> CreditCard:
    values = data.model_dump(exclude_unset=True)
    if values.get("payment_account_id") is not None:
        get_account(session, user, values["payment_account_id"])
    for name, value in values.items():
        setattr(card, name, value)
    session.commit()
    return card


def set_card_archived(session: Session, card: CreditCard, archived: bool) -> CreditCard:
    return _set_archived(session, card, archived)


def delete_card(session: Session, card: CreditCard) -> None:
    """F8: only cards without transactions can be deleted."""
    used = session.scalar(
        select(func.count()).select_from(Transaction).where(Transaction.credit_card_id == card.id)
    )
    if used:
        raise DomainError(
            "Card has transactions; archive it instead.",
            code="finance.card_in_use",
            details={"transactions_count": used},
        )
    session.delete(card)
    session.commit()


def _invoice_exists(session: Session, card: CreditCard, closing_on: date) -> bool:
    """An invoice is any closing date of the card's current `closing_day`, or a date that
    already has transactions (purchases keep their invoice when the closing day changes)."""
    if rules.is_closing_date(closing_on, card.closing_day):
        return True
    return (
        session.scalar(
            select(Transaction.id)
            .where(
                Transaction.credit_card_id == card.id,
                Transaction.invoice_closing_on == closing_on,
            )
            .limit(1)
        )
        is not None
    )


def list_invoices(session: Session, user: User, card: CreditCard) -> list[InvoiceRead]:
    """Every invoice with transactions plus the current one, newest first."""
    lookup = lookup_for(session, user)
    today = moment_for(session, user).today
    totals = _invoice_totals(session, user, [card.id])
    closings = {closing for _, closing in totals} | {_current_closing(card, today)}
    return [
        _invoice_read(card, closing, totals.get((card.id, closing), InvoiceTotals()), today, lookup)
        for closing in sorted(closings, reverse=True)
    ]


def get_invoice(session: Session, user: User, card: CreditCard, closing_on: date) -> InvoiceDetail:
    if not _invoice_exists(session, card, closing_on):
        raise NotFoundError(details={"resource": "invoice"})
    lookup = lookup_for(session, user)
    today = moment_for(session, user).today
    totals = _invoice_totals(session, user, [card.id]).get((card.id, closing_on), InvoiceTotals())
    items = list(
        session.scalars(
            select(Transaction)
            .where(
                Transaction.user_id == user.id,
                Transaction.credit_card_id == card.id,
                Transaction.invoice_closing_on == closing_on,
            )
            .order_by(*_NEWEST_FIRST)
        )
    )
    reads = transaction_reads(lookup, items)
    invoice = _invoice_read(card, closing_on, totals, today, lookup)
    return InvoiceDetail(
        **invoice.model_dump(),
        card=card_ref(card),
        transactions=[r for r in reads if r.kind == EXPENSE],
        payments=[r for r in reads if r.kind == CARD_PAYMENT],
    )


def pay_invoice(
    session: Session, user: User, card: CreditCard, closing_on: date, data: InvoicePaymentCreate
) -> Transaction:
    """F5: a `card_payment` from an account; partial payments are allowed."""
    if not _invoice_exists(session, card, closing_on):
        raise NotFoundError(details={"resource": "invoice"})
    account = get_account(session, user, data.account_id)
    transaction = Transaction(
        id=data.id or uuid7(),
        user_id=user.id,
        kind=CARD_PAYMENT,
        amount_cents=data.amount_cents,
        occurred_on=data.occurred_on or moment_for(session, user).today,
        occurred_time=data.occurred_time,
        description=data.description,
        account_id=account.id,
        credit_card_id=card.id,
        invoice_closing_on=closing_on,
    )
    session.add(transaction)
    session.commit()
    return transaction


# ---------------------------------------------------------------- transactions (F3, F4, F10, F13)

_NEWEST_FIRST = (
    Transaction.occurred_on.desc(),
    Transaction.occurred_time.desc().nulls_last(),
    Transaction.created_at.desc(),
    Transaction.id.desc(),
)

_REFERENCES = (
    "account_id",
    "destination_account_id",
    "credit_card_id",
    "category_id",
    "invoice_closing_on",
)


def get_transaction(session: Session, user: User, transaction_id: UUID) -> Transaction:
    transaction = session.scalar(
        select(Transaction).where(Transaction.id == transaction_id, Transaction.user_id == user.id)
    )
    if transaction is None:
        raise NotFoundError()
    return transaction


@dataclass
class Draft:
    """The fields of a transaction being created or updated, validated together."""

    kind: TransactionKind
    amount_cents: int
    occurred_on: date
    description: str
    account_id: UUID | None = None
    destination_account_id: UUID | None = None
    credit_card_id: UUID | None = None
    category_id: UUID | None = None
    invoice_closing_on: date | None = None


def _required(draft: Draft) -> set[str]:
    """The combinations of docs/dominio.md (Finanças)."""
    match draft.kind:
        case TransactionKind.INCOME:
            return {"account_id", "category_id"}
        case TransactionKind.EXPENSE:
            return {"category_id", "credit_card_id" if draft.credit_card_id else "account_id"}
        case TransactionKind.TRANSFER:
            return {"account_id", "destination_account_id"}
        case TransactionKind.CARD_PAYMENT:
            return {"account_id", "credit_card_id", "invoice_closing_on"}
        case TransactionKind.ADJUSTMENT:
            return {"account_id"}


def _validate(session: Session, user: User, draft: Draft) -> CreditCard | None:
    """Checks a draft and fills the derived invoice of card expenses (F4). Returns the card."""
    required = _required(draft)
    missing = sorted(field for field in required if getattr(draft, field) is None)
    if draft.kind in (INCOME, EXPENSE) and not draft.description:
        missing.append("description")
    unexpected = sorted(
        field
        for field in _REFERENCES
        if field not in required and getattr(draft, field) is not None
    )
    if missing or unexpected:
        raise DomainError(
            "Invalid fields for this kind of transaction.",
            code="finance.invalid_combination",
            details={"kind": draft.kind.value, "missing": missing, "unexpected": unexpected},
        )
    if (draft.kind == ADJUSTMENT and draft.amount_cents == 0) or (
        draft.kind != ADJUSTMENT and draft.amount_cents <= 0
    ):
        raise DomainError(
            "Amount must be positive (non-zero for adjustments).", code="finance.invalid_amount"
        )
    if draft.account_id is not None:
        get_account(session, user, draft.account_id)
    if draft.destination_account_id is not None:
        get_account(session, user, draft.destination_account_id)
        if draft.destination_account_id == draft.account_id:
            raise DomainError("Choose two different accounts.", code="finance.same_account")
    if draft.category_id is not None:
        category = get_category(session, user, draft.category_id)
        if category.kind.value != draft.kind.value:
            raise DomainError(
                "The category is of another kind.", code="finance.category_kind_mismatch"
            )
    card = None
    if draft.credit_card_id is not None:
        card = get_card(session, user, draft.credit_card_id)
        if draft.kind == EXPENSE:
            draft.invoice_closing_on = rules.invoice_closing_for(
                draft.occurred_on, card.closing_day
            )
        elif draft.invoice_closing_on is not None and not _invoice_exists(
            session, card, draft.invoice_closing_on
        ):
            raise DomainError("Not an invoice of this card.", code="finance.invalid_invoice")
    return card


def create_transaction(session: Session, user: User, data: TransactionCreate) -> Transaction:
    """Creates a transaction; a card expense with `installments` creates one per installment
    (F10) and returns the first."""
    if data.installments and not (data.kind == EXPENSE and data.credit_card_id):
        raise DomainError(
            "Installments are only for card expenses.", code="finance.installments_require_card"
        )
    if data.kind == EXPENSE and data.invoice_closing_on is not None:
        _invalid_invoice_field(data.kind)
    draft = Draft(
        kind=data.kind,
        amount_cents=data.amount_cents,
        occurred_on=data.occurred_on,
        description=data.description,
        **{field: getattr(data, field) for field in _REFERENCES},
    )
    card = _validate(session, user, draft)
    common = {
        "user_id": user.id,
        "kind": data.kind,
        "occurred_time": data.occurred_time,
        "description": data.description,
        "notes": data.notes,
        "account_id": draft.account_id,
        "destination_account_id": draft.destination_account_id,
        "credit_card_id": draft.credit_card_id,
        "category_id": draft.category_id,
    }
    if not data.installments or card is None:
        transaction = Transaction(
            **common,
            id=data.id or uuid7(),
            amount_cents=draft.amount_cents,
            occurred_on=draft.occurred_on,
            invoice_closing_on=draft.invoice_closing_on,
        )
        session.add(transaction)
        session.commit()
        return transaction

    assert draft.invoice_closing_on is not None
    group = uuid7()
    count = data.installments
    first_invoice = draft.invoice_closing_on
    installments = [
        Transaction(
            **common,
            id=(data.id or uuid7()) if index == 0 else uuid7(),
            amount_cents=amount,
            occurred_on=on,
            invoice_closing_on=_nth_closing(first_invoice, index, card.closing_day),
            installment_group_id=group,
            installment_number=index + 1,
            installment_count=count,
        )
        for index, (amount, on) in enumerate(
            zip(
                rules.split_installments(draft.amount_cents, count),
                rules.installment_dates(draft.occurred_on, count),
                strict=True,
            )
        )
    ]
    session.add_all(installments)
    session.commit()
    return installments[0]


def _nth_closing(first: date, index: int, closing_day: int) -> date:
    """F10: installment k goes to the k-th invoice from the purchase's invoice."""
    month = add_months(first.replace(day=1), index)
    return rules.closing_date(month.year, month.month, closing_day)


def _invalid_invoice_field(kind: TransactionKind) -> None:
    raise DomainError(
        "Invalid fields for this kind of transaction.",
        code="finance.invalid_combination",
        details={"kind": kind.value, "missing": [], "unexpected": ["invoice_closing_on"]},
    )


def update_transaction(
    session: Session, user: User, transaction: Transaction, data: TransactionUpdate
) -> Transaction:
    """F16: the kind never changes. Card expenses get their invoice recomputed (F4)."""
    values = data.model_dump(exclude_unset=True)
    if "invoice_closing_on" in values and transaction.kind != CARD_PAYMENT:
        _invalid_invoice_field(transaction.kind)
    draft = Draft(
        kind=transaction.kind,
        amount_cents=values.get("amount_cents", transaction.amount_cents),
        occurred_on=values.get("occurred_on", transaction.occurred_on),
        description=values.get("description", transaction.description),
        **{field: values.get(field, getattr(transaction, field)) for field in _REFERENCES},
    )
    if draft.kind == EXPENSE:
        draft.invoice_closing_on = None
    if transaction.installment_group_id is not None and draft.credit_card_id is None:
        raise DomainError(
            "Installments are only for card expenses.", code="finance.installments_require_card"
        )
    _validate(session, user, draft)
    for name in ("occurred_time", "notes"):
        if name in values:
            setattr(transaction, name, values[name])
    transaction.amount_cents = draft.amount_cents
    transaction.occurred_on = draft.occurred_on
    transaction.description = draft.description
    for name in _REFERENCES:
        setattr(transaction, name, getattr(draft, name))
    session.commit()
    return transaction


def delete_transaction(
    session: Session, user: User, transaction: Transaction, *, all_installments: bool = False
) -> None:
    if all_installments and transaction.installment_group_id is not None:
        session.execute(
            delete(Transaction).where(
                Transaction.user_id == user.id,
                Transaction.installment_group_id == transaction.installment_group_id,
            )
        )
    else:
        session.delete(transaction)
    session.commit()


def transaction_reads(lookup: Lookup, items: Iterable[Transaction]) -> list[TransactionRead]:
    return [
        TransactionRead(
            id=t.id,
            kind=t.kind,
            amount_cents=t.amount_cents,
            occurred_on=t.occurred_on,
            occurred_time=t.occurred_time,
            description=t.description,
            notes=t.notes,
            account=lookup.account(t.account_id),
            destination_account=lookup.account(t.destination_account_id),
            credit_card=lookup.card(t.credit_card_id),
            category=lookup.category(t.category_id),
            invoice_closing_on=t.invoice_closing_on,
            installment_group_id=t.installment_group_id,
            installment_number=t.installment_number,
            installment_count=t.installment_count,
            created_at=t.created_at,
            updated_at=t.updated_at,
        )
        for t in items
    ]


def transaction_read(session: Session, user: User, transaction: Transaction) -> TransactionRead:
    return transaction_reads(lookup_for(session, user), [transaction])[0]


@dataclass(frozen=True)
class TransactionFilters:
    date_from: date | None = None
    date_to: date | None = None
    kind: TransactionKind | None = None
    account_id: UUID | None = None
    credit_card_id: UUID | None = None
    category_id: UUID | None = None
    q: str | None = None


def _escape_like(text: str) -> str:
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _conditions(user: User, filters: TransactionFilters) -> list[ColumnElement[bool]]:
    conditions: list[ColumnElement[bool]] = [Transaction.user_id == user.id]
    if filters.date_from is not None:
        conditions.append(Transaction.occurred_on >= filters.date_from)
    if filters.date_to is not None:
        conditions.append(Transaction.occurred_on <= filters.date_to)
    if filters.kind is not None:
        conditions.append(Transaction.kind == filters.kind)
    if filters.account_id is not None:
        conditions.append(
            or_(
                Transaction.account_id == filters.account_id,
                Transaction.destination_account_id == filters.account_id,
            )
        )
    if filters.credit_card_id is not None:
        conditions.append(Transaction.credit_card_id == filters.credit_card_id)
    if filters.category_id is not None:
        conditions.append(Transaction.category_id == filters.category_id)
    if filters.q and (text := filters.q.strip()):
        pattern = f"%{_escape_like(text)}%"
        matches = [
            Transaction.description.ilike(pattern, escape="\\"),
            Transaction.notes.ilike(pattern, escape="\\"),
        ]
        if (amounts := rules.amount_range(text)) is not None:
            matches.append(func.abs(Transaction.amount_cents).between(*amounts))
        conditions.append(or_(*matches))
    return conditions


TRANSACTION_SORT = {"occurred_on": Transaction.occurred_on, "amount": Transaction.amount_cents}


def list_transactions(
    session: Session,
    user: User,
    page: PageParams,
    filters: TransactionFilters,
    *,
    sort: Sort | None = None,
    updated_since: datetime | None = None,
) -> TransactionPage:
    conditions = _conditions(user, filters)
    if updated_since is not None:
        conditions.append(Transaction.updated_at > updated_since)
    result = paginate(
        session,
        select(Transaction).where(*conditions),
        page,
        sort=sort or Sort("occurred_on", descending=True),
        sort_columns=TRANSACTION_SORT,
        tiebreaker=_NEWEST_FIRST[1:],
        updated_since=updated_since,
    )
    income, expense = session.execute(
        select(
            func.coalesce(func.sum(Transaction.amount_cents).filter(Transaction.kind == INCOME), 0),
            func.coalesce(
                func.sum(Transaction.amount_cents).filter(Transaction.kind == EXPENSE), 0
            ),
        ).where(*conditions)
    ).one()
    return TransactionPage(
        items=transaction_reads(lookup_for(session, user), result.items),
        total=result.total,
        limit=page.limit,
        offset=page.offset,
        income_cents=int(income),
        expense_cents=int(expense),
    )


# ---------------------------------------------------------------- overview and Início (F12, F15)


def _report_conditions(user: User, start: date, until: date) -> list[ColumnElement[bool]]:
    """F3: income and expenses by competence (card purchases on the purchase date)."""
    return [
        Transaction.user_id == user.id,
        Transaction.kind.in_([INCOME, EXPENSE]),
        Transaction.occurred_on.between(start, until),
    ]


def _month_totals(session: Session, user: User, start: date, until: date) -> tuple[int, int]:
    totals = {
        kind: int(total)
        for kind, total in session.execute(
            select(Transaction.kind, func.sum(Transaction.amount_cents))
            .where(*_report_conditions(user, start, until))
            .group_by(Transaction.kind)
        )
    }
    return int(totals.get(INCOME, 0)), int(totals.get(EXPENSE, 0))


def _series(session: Session, user: User, first: date, until: date) -> list[MonthPoint]:
    start = add_months(first, -(SERIES_MONTHS - 1))
    month = func.to_char(Transaction.occurred_on, "YYYY-MM")
    rows = session.execute(
        select(month, Transaction.kind, func.sum(Transaction.amount_cents))
        .where(*_report_conditions(user, start, until))
        .group_by(month, Transaction.kind)
    )
    values = {(m, kind): int(total) for m, kind, total in rows}
    months = [add_months(start, index).strftime("%Y-%m") for index in range(SERIES_MONTHS)]
    return [
        MonthPoint(
            month=m,
            income_cents=values.get((m, INCOME), 0),
            expense_cents=values.get((m, EXPENSE), 0),
        )
        for m in months
    ]


def _category_shares(
    session: Session,
    user: User,
    lookup: Lookup,
    kind: TransactionKind,
    start: date,
    until: date,
) -> list[CategoryShare]:
    rows = list(
        session.execute(
            select(Transaction.category_id, func.sum(Transaction.amount_cents), func.count())
            .where(*_report_conditions(user, start, until), Transaction.kind == kind)
            .group_by(Transaction.category_id)
        )
    )
    total = sum(int(amount) for _, amount, _ in rows)
    shares = [
        CategoryShare(
            category=category_ref(lookup.categories[category_id]),
            amount_cents=int(amount),
            percent=rules.percent(int(amount), total) or 0,
            transactions_count=count,
        )
        for category_id, amount, count in rows
        if category_id is not None
    ]
    shares.sort(key=lambda share: (-share.amount_cents, share.category.name))
    return shares


def _open_invoices(session: Session, user: User, lookup: Lookup, today: date) -> list[OpenInvoice]:
    """Unpaid invoices up to the current one of each active card, by due date."""
    cards = [card for card in lookup.cards.values() if card.archived_at is None]
    totals = _invoice_totals(session, user, [card.id for card in cards])
    items: list[OpenInvoice] = []
    for card in cards:
        current = _current_closing(card, today)
        available = card.limit_cents - _used(totals, card)
        for (card_id, closing), entry in sorted(totals.items(), key=lambda item: item[0][1]):
            if card_id != card.id or closing > current or entry.amount <= entry.paid:
                continue
            items.append(
                OpenInvoice(
                    card=card_ref(card),
                    limit_cents=card.limit_cents,
                    available_limit_cents=available,
                    invoice=_invoice_read(card, closing, entry, today, lookup),
                )
            )
    items.sort(key=lambda item: (item.invoice.due_on, item.card.name))
    return items


@dataclass(frozen=True)
class MonthReport:
    first: date
    until: date
    lookup: Lookup
    accounts: list[AccountBalance]
    total_balance_cents: int
    accounts_count: int
    income_cents: int
    expense_cents: int
    expenses_by_category: list[CategoryShare]
    open_invoices: list[OpenInvoice]


def _month_report(session: Session, user: User, moment: Moment, first: date) -> MonthReport:
    until = _until(first, moment)
    lookup = lookup_for(session, user)
    active = [a for a in lookup.accounts.values() if a.archived_at is None]
    balance = balances(session, user, active, until)
    income, expense = _month_totals(session, user, first, until)
    return MonthReport(
        first=first,
        until=until,
        lookup=lookup,
        accounts=[
            AccountBalance(account=account_ref(a), balance_cents=balance[a.id]) for a in active
        ],
        total_balance_cents=sum(balance[a.id] for a in active if a.include_in_total),
        accounts_count=sum(1 for a in active if a.include_in_total),
        income_cents=income,
        expense_cents=expense,
        expenses_by_category=_category_shares(session, user, lookup, EXPENSE, first, until),
        open_invoices=_open_invoices(session, user, lookup, moment.today),
    )


def overview(session: Session, user: User, month: str | None = None) -> FinanceOverview:
    moment = moment_for(session, user)
    report = _month_report(session, user, moment, parse_month(month, moment))
    return FinanceOverview(
        month=report.first.strftime("%Y-%m"),
        until=report.until,
        total_balance_cents=report.total_balance_cents,
        accounts_count=report.accounts_count,
        accounts=report.accounts,
        income_cents=report.income_cents,
        expense_cents=report.expense_cents,
        expense_percent=rules.percent(report.expense_cents, report.income_cents),
        result_cents=report.income_cents - report.expense_cents,
        series=_series(session, user, report.first, report.until),
        expenses_by_category=report.expenses_by_category,
        income_by_category=_category_shares(
            session, user, report.lookup, INCOME, report.first, report.until
        ),
        open_invoices=report.open_invoices,
    )


def build_summary(session: Session, user: User) -> FinanceSummary:
    moment = moment_for(session, user)
    report = _month_report(session, user, moment, moment.month_start)
    return FinanceSummary(
        month=report.first.strftime("%Y-%m"),
        total_balance_cents=report.total_balance_cents,
        accounts=report.accounts,
        income_cents=report.income_cents,
        expense_cents=report.expense_cents,
        expense_percent=rules.percent(report.expense_cents, report.income_cents),
        expenses_by_category=report.expenses_by_category,
        next_invoice=report.open_invoices[0] if report.open_invoices else None,
    )


def build_upcoming(session: Session, user: User) -> list[UpcomingItem]:
    """F15: closing (while open) and due date of every unpaid invoice."""
    today = moment_for(session, user).today
    items: list[UpcomingItem] = []
    for open_invoice in _open_invoices(session, user, lookup_for(session, user), today):
        invoice, card = open_invoice.invoice, open_invoice.card
        if invoice.status == "open":
            items.append(
                UpcomingItem(
                    module="finance",
                    kind="finance.invoice_closing",
                    on=invoice.closing_on,
                    subject=card.name,
                    entity_id=card.id,
                    data={
                        "amount_cents": invoice.amount_cents,
                        "available_limit_cents": open_invoice.available_limit_cents,
                    },
                )
            )
        items.append(
            UpcomingItem(
                module="finance",
                kind="finance.invoice_due",
                on=invoice.due_on,
                subject=card.name,
                entity_id=card.id,
                data={
                    "amount_cents": invoice.amount_cents,
                    "paid_cents": invoice.paid_cents,
                    "remaining_cents": invoice.remaining_cents,
                    "status": invoice.status,
                },
            )
        )
    return items


def _occurred_at(transaction: Transaction, tz: ZoneInfo) -> datetime:
    """The moment of a transaction for "Atividade recente": its time, or when it was recorded
    if that was on the same day, or the start of the day."""
    if transaction.occurred_time is not None:
        return datetime.combine(transaction.occurred_on, transaction.occurred_time, tz)
    if transaction.created_at.astimezone(tz).date() == transaction.occurred_on:
        return transaction.created_at
    return datetime.combine(transaction.occurred_on, time(), tz)


def build_activity(session: Session, user: User) -> list[ActivityItem]:
    """F15: the latest transactions up to today."""
    moment = moment_for(session, user)
    lookup = lookup_for(session, user)
    transactions = session.scalars(
        select(Transaction)
        .where(Transaction.user_id == user.id, Transaction.occurred_on <= moment.today)
        .order_by(*_NEWEST_FIRST)
        .limit(ACTIVITY_LIMIT)
    )

    def name(item: Account | Category | CreditCard | None) -> str | None:
        return item.name if item is not None else None

    return [
        ActivityItem(
            module="finance",
            kind="finance.transaction",
            occurred_at=_occurred_at(t, moment.tz),
            subject=t.description,
            entity_id=t.id,
            data={
                "transaction_kind": t.kind.value,
                "amount_cents": t.amount_cents,
                "category": name(lookup.categories.get(t.category_id) if t.category_id else None),
                "account": name(lookup.accounts.get(t.account_id) if t.account_id else None),
                "destination_account": name(
                    lookup.accounts.get(t.destination_account_id)
                    if t.destination_account_id
                    else None
                ),
                "credit_card": name(
                    lookup.cards.get(t.credit_card_id) if t.credit_card_id else None
                ),
                "occurred_time": t.occurred_time.strftime("%H:%M") if t.occurred_time else None,
            },
        )
        for t in transactions
    ]
