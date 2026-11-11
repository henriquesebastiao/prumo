"""Studies tables in the user data export (D38)."""

from sqlalchemy.orm import Session

from prumo.core.export import ModuleExport, table_rows
from prumo.modules.studies.models import (
    PlanBlock,
    StudyArea,
    StudyPlan,
    StudySession,
    Subject,
    Topic,
)
from prumo.system.users.models import User


def build_export(session: Session, user: User) -> ModuleExport:
    return ModuleExport(
        tables={
            "areas": table_rows(session, StudyArea, user.id),
            "subjects": table_rows(session, Subject, user.id),
            "topics": table_rows(session, Topic, user.id),
            "plans": table_rows(session, StudyPlan, user.id),
            "plan_blocks": table_rows(session, PlanBlock, user.id),
            "sessions": table_rows(session, StudySession, user.id),
        }
    )
