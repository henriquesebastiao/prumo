from datetime import date
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from prumo.core.deps import SessionDep
from prumo.core.errors import error_responses
from prumo.core.pagination import PageDep, Sort, sort_param
from prumo.modules.finance import service
from prumo.modules.finance.models import (
    Account,
    Category,
    CategoryKind,
    CreditCard,
    Transaction,
    TransactionKind,
)
from prumo.modules.finance.schemas import (
    AccountCreate,
    AccountList,
    AccountRead,
    AccountUpdate,
    AdjustmentCreate,
    CategoryCreate,
    CategoryList,
    CategoryRead,
    CategoryUpdate,
    CreditCardCreate,
    CreditCardList,
    CreditCardRead,
    CreditCardUpdate,
    FinanceOverview,
    InvoiceDetail,
    InvoiceList,
    InvoicePaymentCreate,
    Month,
    TransactionCreate,
    TransactionPage,
    TransactionRead,
    TransactionUpdate,
)
from prumo.system.auth.deps import CurrentUser

router = APIRouter(responses=error_responses(401, 403, 404, 422))

Archived = Literal["false", "true", "all"]
TransactionSort = Annotated[
    Sort, Depends(sort_param("occurred_on", "amount", default="-occurred_on"))
]


def _account(account_id: UUID, session: SessionDep, user: CurrentUser) -> Account:
    return service.get_account(session, user, account_id)


def _category(category_id: UUID, session: SessionDep, user: CurrentUser) -> Category:
    return service.get_category(session, user, category_id)


def _card(card_id: UUID, session: SessionDep, user: CurrentUser) -> CreditCard:
    return service.get_card(session, user, card_id)


def _transaction(transaction_id: UUID, session: SessionDep, user: CurrentUser) -> Transaction:
    return service.get_transaction(session, user, transaction_id)


AccountDep = Annotated[Account, Depends(_account)]
CategoryDep = Annotated[Category, Depends(_category)]
CardDep = Annotated[CreditCard, Depends(_card)]
TransactionDep = Annotated[Transaction, Depends(_transaction)]


# ---------------------------------------------------------------- overview


@router.get("/overview")
def read_overview(
    session: SessionDep,
    user: CurrentUser,
    month: Annotated[
        Month | None, Query(description="`YYYY-MM`; the current month if absent.")
    ] = None,
) -> FinanceOverview:
    """F12: balances, income and expenses of the month, 6-month series, categories, invoices."""
    return service.overview(session, user, month)


# ---------------------------------------------------------------- accounts


@router.get("/accounts")
def list_accounts(
    session: SessionDep, user: CurrentUser, archived: Archived = "false"
) -> AccountList:
    return service.list_accounts(session, user, archived=archived)


@router.post("/accounts", status_code=status.HTTP_201_CREATED)
def create_account(data: AccountCreate, session: SessionDep, user: CurrentUser) -> AccountRead:
    return service.account_read(session, user, service.create_account(session, user, data))


@router.get("/accounts/{account_id}")
def read_account(account: AccountDep, session: SessionDep, user: CurrentUser) -> AccountRead:
    return service.account_read(session, user, account)


@router.patch("/accounts/{account_id}")
def update_account(
    data: AccountUpdate, account: AccountDep, session: SessionDep, user: CurrentUser
) -> AccountRead:
    return service.account_read(session, user, service.update_account(session, account, data))


@router.delete("/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(account: AccountDep, session: SessionDep) -> None:
    """F8: only without transactions (`finance.account_in_use`); otherwise archive."""
    service.delete_account(session, account)


@router.post("/accounts/{account_id}/archive")
def archive_account(account: AccountDep, session: SessionDep, user: CurrentUser) -> AccountRead:
    return service.account_read(
        session, user, service.set_account_archived(session, account, archived=True)
    )


@router.post("/accounts/{account_id}/unarchive")
def unarchive_account(account: AccountDep, session: SessionDep, user: CurrentUser) -> AccountRead:
    return service.account_read(
        session, user, service.set_account_archived(session, account, archived=False)
    )


@router.post("/accounts/{account_id}/adjustments", status_code=status.HTTP_201_CREATED)
def adjust_balance(
    data: AdjustmentCreate, account: AccountDep, session: SessionDep, user: CurrentUser
) -> TransactionRead:
    """F11: records an `adjustment` with the difference to the real balance."""
    transaction = service.adjust_balance(session, user, account, data)
    return service.transaction_read(session, user, transaction)


# ---------------------------------------------------------------- categories


@router.get("/categories")
def list_categories(
    session: SessionDep,
    user: CurrentUser,
    kind: CategoryKind | None = None,
    archived: Archived = "false",
    month: Annotated[Month | None, Query(description="Month of the counts and totals.")] = None,
) -> CategoryList:
    return service.list_categories(session, user, kind=kind, archived=archived, month=month)


@router.post("/categories", status_code=status.HTTP_201_CREATED, responses=error_responses(409))
def create_category(data: CategoryCreate, session: SessionDep, user: CurrentUser) -> CategoryRead:
    return service.category_read(session, user, service.create_category(session, user, data))


@router.get("/categories/{category_id}")
def read_category(category: CategoryDep, session: SessionDep, user: CurrentUser) -> CategoryRead:
    return service.category_read(session, user, category)


@router.patch("/categories/{category_id}", responses=error_responses(409))
def update_category(
    data: CategoryUpdate, category: CategoryDep, session: SessionDep, user: CurrentUser
) -> CategoryRead:
    return service.category_read(
        session, user, service.update_category(session, user, category, data)
    )


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category: CategoryDep, session: SessionDep) -> None:
    """F8: only unused categories (`finance.category_in_use`); otherwise archive."""
    service.delete_category(session, category)


@router.post("/categories/{category_id}/archive")
def archive_category(category: CategoryDep, session: SessionDep, user: CurrentUser) -> CategoryRead:
    return service.category_read(
        session, user, service.set_category_archived(session, category, archived=True)
    )


@router.post("/categories/{category_id}/unarchive")
def unarchive_category(
    category: CategoryDep, session: SessionDep, user: CurrentUser
) -> CategoryRead:
    return service.category_read(
        session, user, service.set_category_archived(session, category, archived=False)
    )


# ---------------------------------------------------------------- transactions


@router.get("/transactions")
def list_transactions(
    session: SessionDep,
    user: CurrentUser,
    page: PageDep,
    sort: TransactionSort,
    date_from: Annotated[date | None, Query(alias="from")] = None,
    date_to: Annotated[date | None, Query(alias="to")] = None,
    kind: TransactionKind | None = None,
    account_id: Annotated[UUID | None, Query(description="Source or destination account.")] = None,
    credit_card_id: UUID | None = None,
    category_id: UUID | None = None,
    q: Annotated[
        str | None, Query(max_length=120, description="Description, notes or value (F13).")
    ] = None,
) -> TransactionPage:
    filters = service.TransactionFilters(
        date_from=date_from,
        date_to=date_to,
        kind=kind,
        account_id=account_id,
        credit_card_id=credit_card_id,
        category_id=category_id,
        q=q,
    )
    return service.list_transactions(session, user, page, filters, sort=sort)


@router.post("/transactions", status_code=status.HTTP_201_CREATED)
def create_transaction(
    data: TransactionCreate, session: SessionDep, user: CurrentUser
) -> TransactionRead:
    """Validates the fields of each `kind` (docs/dominio.md). With `installments`, creates every
    installment and returns the first (F10)."""
    transaction = service.create_transaction(session, user, data)
    return service.transaction_read(session, user, transaction)


@router.get("/transactions/{transaction_id}")
def read_transaction(
    transaction: TransactionDep, session: SessionDep, user: CurrentUser
) -> TransactionRead:
    return service.transaction_read(session, user, transaction)


@router.patch("/transactions/{transaction_id}")
def update_transaction(
    data: TransactionUpdate, transaction: TransactionDep, session: SessionDep, user: CurrentUser
) -> TransactionRead:
    updated = service.update_transaction(session, user, transaction, data)
    return service.transaction_read(session, user, updated)


@router.delete("/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction: TransactionDep,
    session: SessionDep,
    user: CurrentUser,
    installments: Annotated[
        Literal["one", "all"], Query(description="`all` removes the whole installment purchase.")
    ] = "one",
) -> None:
    service.delete_transaction(session, user, transaction, all_installments=installments == "all")


# ---------------------------------------------------------------- credit cards and invoices


@router.get("/credit-cards")
def list_cards(
    session: SessionDep, user: CurrentUser, archived: Archived = "false"
) -> CreditCardList:
    return CreditCardList(items=service.list_cards(session, user, archived=archived))


@router.post("/credit-cards", status_code=status.HTTP_201_CREATED)
def create_card(data: CreditCardCreate, session: SessionDep, user: CurrentUser) -> CreditCardRead:
    return service.card_read(session, user, service.create_card(session, user, data))


@router.get("/credit-cards/{card_id}")
def read_card(card: CardDep, session: SessionDep, user: CurrentUser) -> CreditCardRead:
    return service.card_read(session, user, card)


@router.patch("/credit-cards/{card_id}")
def update_card(
    data: CreditCardUpdate, card: CardDep, session: SessionDep, user: CurrentUser
) -> CreditCardRead:
    return service.card_read(session, user, service.update_card(session, user, card, data))


@router.delete("/credit-cards/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_card(card: CardDep, session: SessionDep) -> None:
    """F8: only without transactions (`finance.card_in_use`); otherwise archive."""
    service.delete_card(session, card)


@router.post("/credit-cards/{card_id}/archive")
def archive_card(card: CardDep, session: SessionDep, user: CurrentUser) -> CreditCardRead:
    return service.card_read(session, user, service.set_card_archived(session, card, archived=True))


@router.post("/credit-cards/{card_id}/unarchive")
def unarchive_card(card: CardDep, session: SessionDep, user: CurrentUser) -> CreditCardRead:
    return service.card_read(
        session, user, service.set_card_archived(session, card, archived=False)
    )


@router.get("/credit-cards/{card_id}/invoices")
def list_invoices(card: CardDep, session: SessionDep, user: CurrentUser) -> InvoiceList:
    """Every invoice with transactions plus the current one, newest first (F5)."""
    return InvoiceList(items=service.list_invoices(session, user, card))


@router.get("/credit-cards/{card_id}/invoices/{closing_on}")
def read_invoice(
    closing_on: date, card: CardDep, session: SessionDep, user: CurrentUser
) -> InvoiceDetail:
    return service.get_invoice(session, user, card, closing_on)


@router.post(
    "/credit-cards/{card_id}/invoices/{closing_on}/payments", status_code=status.HTTP_201_CREATED
)
def pay_invoice(
    closing_on: date,
    data: InvoicePaymentCreate,
    card: CardDep,
    session: SessionDep,
    user: CurrentUser,
) -> TransactionRead:
    """Records a `card_payment` (total or partial) from an account."""
    transaction = service.pay_invoice(session, user, card, closing_on, data)
    return service.transaction_read(session, user, transaction)
