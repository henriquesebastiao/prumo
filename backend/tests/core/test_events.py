from collections.abc import Iterator
from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from prumo.core.events import EventBus, publish
from prumo.core.modules import registry
from prumo.main import bootstrap
from prumo.system.preferences.schemas import PreferencesUpdate
from prumo.system.preferences.service import update_preferences
from prumo.system.users.models import User
from tests import factories
from tests.fakes.modules import TaskCompleted, journal, notes, on_task_completed, tasks


@pytest.fixture(autouse=True)
def fake_modules() -> Iterator[None]:
    bootstrap([tasks, notes])
    journal.clear()
    yield
    journal.clear()
    bootstrap()


def test_handler_receives_published_event(db: Session) -> None:
    user = factories.create_user(db)
    publish(db, TaskCompleted(user_id=user.id, title="Pagar a conta de luz"))
    assert journal.handled_events == ["Pagar a conta de luz"]


def test_handler_is_skipped_when_its_module_is_disabled_for_the_user(db: Session) -> None:
    user = factories.create_user(db)
    update_preferences(db, user, PreferencesUpdate(enabled_modules=["tasks"]))
    publish(db, TaskCompleted(user_id=user.id, title="Ignorado"))
    assert journal.handled_events == []


def test_failing_handler_rolls_back_the_whole_operation(db: Session) -> None:
    journal.fail_on_event = True
    owner = factories.create_user(db, username="dono")
    db.begin_nested()
    db.add(User(username="parcial", display_name="Parcial", password_hash="x"))
    db.flush()
    with pytest.raises(RuntimeError, match="handler failed"):
        publish(db, TaskCompleted(user_id=owner.id, title="Falha"))
    db.rollback()
    assert db.scalar(select(User).where(User.username == "parcial")) is None
    assert db.scalar(select(User).where(User.username == "dono")) is not None


def test_bus_without_subscribers_does_nothing(db: Session) -> None:
    isolated = EventBus()
    isolated.publish(db, TaskCompleted(user_id=UUID(int=1), title="Ninguém ouve"))
    assert journal.handled_events == []


def test_only_exact_event_types_are_dispatched() -> None:
    isolated = EventBus()
    isolated.subscribe(TaskCompleted, on_task_completed, module_id="notes")
    assert len(isolated.handlers_for(TaskCompleted)) == 1
    isolated.reset()
    assert isolated.handlers_for(TaskCompleted) == []


def test_registry_holds_the_fake_modules() -> None:
    assert registry.ids == ("tasks", "notes")
