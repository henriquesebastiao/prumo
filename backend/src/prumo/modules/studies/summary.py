"""Studies data for Início: summary card and "Atividade recente" (E11)."""

from sqlalchemy.orm import Session

from prumo.core.modules import ActivityItem
from prumo.modules.studies import service
from prumo.modules.studies.schemas import StudiesSummary
from prumo.system.users.models import User


def build_summary(session: Session, user: User) -> StudiesSummary:
    return service.build_summary(session, user)


def build_activity(session: Session, user: User) -> list[ActivityItem]:
    return service.build_activity(session, user)
