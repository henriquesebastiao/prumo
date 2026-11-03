"""Finance data for Início: summary card, "Vem aí" and "Atividade recente"."""

from sqlalchemy.orm import Session

from prumo.core.modules import ActivityItem, UpcomingItem
from prumo.modules.finance import service
from prumo.modules.finance.schemas import FinanceSummary
from prumo.system.users.models import User


def build_summary(session: Session, user: User) -> FinanceSummary:
    return service.build_summary(session, user)


def build_upcoming(session: Session, user: User) -> list[UpcomingItem]:
    return service.build_upcoming(session, user)


def build_activity(session: Session, user: User) -> list[ActivityItem]:
    return service.build_activity(session, user)
