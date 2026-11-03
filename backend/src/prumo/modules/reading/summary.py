"""Reading data for Início: summary card and "Atividade recente"."""

from sqlalchemy.orm import Session

from prumo.core.modules import ActivityItem
from prumo.modules.reading import service
from prumo.modules.reading.schemas import ReadingSummary
from prumo.system.users.models import User


def build_summary(session: Session, user: User) -> ReadingSummary:
    return service.build_summary(session, user)


def build_activity(session: Session, user: User) -> list[ActivityItem]:
    return service.build_activity(session, user)
