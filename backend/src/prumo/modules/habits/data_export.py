"""Habits tables in the user data export (D38)."""

from sqlalchemy.orm import Session

from prumo.core.export import ModuleExport, table_rows
from prumo.modules.habits.models import Habit, HabitEntry, HabitFrequency, HabitPause, Relapse
from prumo.system.users.models import User


def build_export(session: Session, user: User) -> ModuleExport:
    return ModuleExport(
        tables={
            "habits": table_rows(session, Habit, user.id),
            "frequencies": table_rows(session, HabitFrequency, user.id),
            "entries": table_rows(session, HabitEntry, user.id),
            "pauses": table_rows(session, HabitPause, user.id),
            "relapses": table_rows(session, Relapse, user.id),
        }
    )
