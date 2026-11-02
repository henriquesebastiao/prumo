"""Fake modules used to test the module contract, the dashboard and the event bus.

`tasks` publishes `TaskCompleted`; `notes` subscribes to it. Neither has tables.
"""

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from typing import Any, Literal

from fastapi import APIRouter
from sqlalchemy.orm import Session

from prumo.core.events import Event
from prumo.core.modules import ActivityItem, ModuleSummary, PrumoModule, UpcomingItem
from prumo.system.auth.deps import CurrentUser


@dataclass
class Journal:
    """Records what the fake modules saw, so tests can assert on it."""

    created_users: list[str] = field(default_factory=list)
    handled_events: list[str] = field(default_factory=list)
    fail_on_event: bool = False

    def clear(self) -> None:
        self.created_users.clear()
        self.handled_events.clear()
        self.fail_on_event = False


journal = Journal()


@dataclass(frozen=True, kw_only=True)
class TaskCompleted(Event):
    title: str


# ---------------------------------------------------------------- tasks

tasks_router = APIRouter()


@tasks_router.get("/ping")
def ping(user: CurrentUser) -> dict[str, str]:
    return {"module": "tasks", "user": user.username}


class TasksSummary(ModuleSummary):
    module: Literal["tasks"] = "tasks"
    open_tasks: int


def tasks_summary(session: Session, user: Any) -> TasksSummary:
    return TasksSummary(open_tasks=3)


def tasks_on_user_created(session: Session, user: Any) -> None:
    journal.created_users.append(user.username)


def tasks_upcoming(session: Session, user: Any) -> list[UpcomingItem]:
    return [
        UpcomingItem(module="tasks", kind="tasks.due", on=date(2026, 11, 20), subject="Relatório"),
        UpcomingItem(module="tasks", kind="tasks.due", on=date(2027, 6, 1), subject="Muito longe"),
    ]


def tasks_activity(session: Session, user: Any) -> list[ActivityItem]:
    return [
        ActivityItem(
            module="tasks",
            kind="tasks.done",
            occurred_at=datetime(2026, 11, 16, 12, tzinfo=UTC),
            subject="Pagar luz",
            data={"points": 3},
        )
    ]


tasks = PrumoModule(
    id="tasks",
    version="1.0.0",
    router=tasks_router,
    summary=tasks_summary,
    on_user_created=tasks_on_user_created,
    upcoming=tasks_upcoming,
    activity=tasks_activity,
)

# ---------------------------------------------------------------- notes

notes_router = APIRouter()


class NotesSummary(ModuleSummary):
    module: Literal["notes"] = "notes"
    latest: str | None


def notes_summary(session: Session, user: Any) -> NotesSummary:
    return NotesSummary(latest="Comprar pão")


def on_task_completed(session: Session, event: TaskCompleted) -> None:
    if journal.fail_on_event:
        msg = "handler failed"
        raise RuntimeError(msg)
    journal.handled_events.append(event.title)


def notes_upcoming(session: Session, user: Any) -> list[UpcomingItem]:
    return [
        UpcomingItem(module="notes", kind="notes.review", on=date(2026, 11, 18), subject="Ideias")
    ]


def notes_activity(session: Session, user: Any) -> list[ActivityItem]:
    return [
        ActivityItem(
            module="notes",
            kind="notes.created",
            occurred_at=datetime(2026, 11, 17, 9, tzinfo=UTC),
            subject="Comprar pão",
        )
    ]


notes = PrumoModule(
    id="notes",
    version="0.3.0",
    router=notes_router,
    summary=notes_summary,
    event_handlers={TaskCompleted: on_task_completed},
    upcoming=notes_upcoming,
    activity=notes_activity,
)

# A module without summary or hooks.
plain = PrumoModule(id="plain", version="0.1.0", router=APIRouter())
