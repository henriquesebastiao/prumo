"""Fake modules used to test the module contract, the dashboard and the event bus.

`tasks` publishes `TaskCompleted`; `notes` subscribes to it. Neither has tables.
"""

from dataclasses import dataclass, field
from typing import Any, Literal

from fastapi import APIRouter
from sqlalchemy.orm import Session

from prumo.core.events import Event
from prumo.core.modules import ModuleSummary, PrumoModule
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


tasks = PrumoModule(
    id="tasks",
    version="1.0.0",
    router=tasks_router,
    summary=tasks_summary,
    on_user_created=tasks_on_user_created,
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


notes = PrumoModule(
    id="notes",
    version="0.3.0",
    router=notes_router,
    summary=notes_summary,
    event_handlers={TaskCompleted: on_task_completed},
)

# A module without summary or hooks.
plain = PrumoModule(id="plain", version="0.1.0", router=APIRouter())
