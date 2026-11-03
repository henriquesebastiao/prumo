"""Finance tables in the user data export (D38)."""

from sqlalchemy.orm import Session

from prumo.core.export import ModuleExport, table_rows
from prumo.modules.finance.models import Account, Category, CreditCard, Transaction
from prumo.system.users.models import User


def build_export(session: Session, user: User) -> ModuleExport:
    return ModuleExport(
        tables={
            "accounts": table_rows(session, Account, user.id),
            "categories": table_rows(session, Category, user.id),
            "credit_cards": table_rows(session, CreditCard, user.id),
            "transactions": table_rows(session, Transaction, user.id),
        }
    )
