"""Habits data for Início: the summary card (H9). Nothing in "Atividade recente" nor "Vem aí"."""

from sqlalchemy.orm import Session

from prumo.modules.habits import service
from prumo.modules.habits.schemas import HabitsSummary
from prumo.system.users.models import User


def build_summary(session: Session, user: User) -> HabitsSummary:
    return service.build_summary(session, user)
