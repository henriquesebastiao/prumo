from datetime import date, datetime, time
from enum import StrEnum
from uuid import UUID

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from prumo.core.db import Base, IdMixin, TimestampMixin, UserOwnedMixin, string_enum


class AccountKind(StrEnum):
    CHECKING = "checking"
    SAVINGS = "savings"
    CASH = "cash"
    INVESTMENT = "investment"
    OTHER = "other"


class CategoryKind(StrEnum):
    INCOME = "income"
    EXPENSE = "expense"


class TransactionKind(StrEnum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"
    CARD_PAYMENT = "card_payment"
    ADJUSTMENT = "adjustment"


class Account(Base, IdMixin, TimestampMixin, UserOwnedMixin):
    __tablename__ = "finance_accounts"

    name: Mapped[str] = mapped_column(String(60))
    kind: Mapped[AccountKind] = mapped_column(string_enum(AccountKind, "account_kind"))
    initial_balance_cents: Mapped[int] = mapped_column(BigInteger, default=0)
    color: Mapped[str] = mapped_column(String(16))
    icon: Mapped[str] = mapped_column(String(32))
    include_in_total: Mapped[bool] = mapped_column(default=True)
    archived_at: Mapped[datetime | None]


class Category(Base, IdMixin, TimestampMixin, UserOwnedMixin):
    __tablename__ = "finance_categories"
    __table_args__ = (
        Index(
            "uq_finance_categories_user_kind_name",
            "user_id",
            "kind",
            text("lower(name)"),
            unique=True,
        ),
    )

    kind: Mapped[CategoryKind] = mapped_column(string_enum(CategoryKind, "category_kind"))
    name: Mapped[str] = mapped_column(String(40))
    color: Mapped[str] = mapped_column(String(16))
    icon: Mapped[str] = mapped_column(String(32))
    archived_at: Mapped[datetime | None]


class CreditCard(Base, IdMixin, TimestampMixin, UserOwnedMixin):
    __tablename__ = "finance_credit_cards"
    __table_args__ = (
        CheckConstraint("limit_cents >= 0", name="limit_positive"),
        CheckConstraint("closing_day BETWEEN 1 AND 31", name="closing_day_range"),
        CheckConstraint("due_day BETWEEN 1 AND 31", name="due_day_range"),
    )

    name: Mapped[str] = mapped_column(String(60))
    limit_cents: Mapped[int] = mapped_column(BigInteger)
    closing_day: Mapped[int]
    due_day: Mapped[int]
    payment_account_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("finance_accounts.id", ondelete="SET NULL"), index=True
    )
    color: Mapped[str] = mapped_column(String(16))
    archived_at: Mapped[datetime | None]


class Transaction(Base, IdMixin, TimestampMixin, UserOwnedMixin):
    __tablename__ = "finance_transactions"
    __table_args__ = (
        Index("ix_finance_transactions_user_day", "user_id", "occurred_on"),
        Index("ix_finance_transactions_card_invoice", "credit_card_id", "invoice_closing_on"),
        Index("ix_finance_transactions_installment_group", "installment_group_id"),
        CheckConstraint(
            "amount_cents > 0 OR (kind = 'adjustment' AND amount_cents <> 0)",
            name="amount_sign",
        ),
        CheckConstraint(
            "(installment_group_id IS NULL) = (installment_number IS NULL)"
            " AND (installment_group_id IS NULL) = (installment_count IS NULL)",
            name="installment_fields",
        ),
    )

    kind: Mapped[TransactionKind] = mapped_column(string_enum(TransactionKind, "transaction_kind"))
    amount_cents: Mapped[int] = mapped_column(BigInteger)
    occurred_on: Mapped[date]
    occurred_time: Mapped[time | None]
    description: Mapped[str] = mapped_column(String(120), default="")
    notes: Mapped[str | None] = mapped_column(Text)
    account_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("finance_accounts.id", ondelete="RESTRICT"), index=True
    )
    destination_account_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("finance_accounts.id", ondelete="RESTRICT"), index=True
    )
    credit_card_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("finance_credit_cards.id", ondelete="RESTRICT")
    )
    category_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("finance_categories.id", ondelete="RESTRICT"), index=True
    )
    # Card expenses and card payments: the closing date of their invoice (F4, F5).
    invoice_closing_on: Mapped[date | None]
    installment_group_id: Mapped[UUID | None]
    installment_number: Mapped[int | None]
    installment_count: Mapped[int | None]
