from typing import Any, Literal

import pytest
from fastapi import APIRouter
from sqlalchemy.orm import Session

from prumo.core.events import bus
from prumo.core.modules import ModuleRegistry, ModuleSummary, PrumoModule
from tests.fakes.modules import TaskCompleted, notes, plain, tasks


def test_module_id_must_be_a_stable_identifier() -> None:
    for bad in ("Finance", "1finance", "fi-nance", "x"):
        with pytest.raises(ValueError, match="Invalid module id"):
            PrumoModule(id=bad, version="1", router=APIRouter())


def test_summary_schema_comes_from_the_return_annotation() -> None:
    assert tasks.summary_schema is not None
    assert tasks.summary_schema.__name__ == "TasksSummary"
    assert plain.summary_schema is None


def test_summary_must_return_a_module_summary_for_its_own_id() -> None:
    class WrongSummary(ModuleSummary):
        module: Literal["other"] = "other"

    def wrong(session: Session, user: Any) -> WrongSummary:
        return WrongSummary()

    def untyped(session: Session, user: Any):  # type: ignore[no-untyped-def]
        return None

    with pytest.raises(TypeError, match="must be Literal"):
        PrumoModule(id="mine", version="1", router=APIRouter(), summary=wrong)
    with pytest.raises(TypeError, match="must be annotated"):
        PrumoModule(id="mine", version="1", router=APIRouter(), summary=untyped)


def test_registry_keeps_order_rejects_duplicates_and_subscribes_handlers() -> None:
    registry = ModuleRegistry()
    registry.install([notes, tasks])
    assert registry.ids == ("notes", "tasks")
    assert registry.get("tasks") is tasks
    assert registry.get("missing") is None
    assert [module_id for module_id, _ in bus.handlers_for(TaskCompleted)] == ["notes"]

    with pytest.raises(ValueError, match="Duplicate module ids: tasks"):
        registry.install([tasks, tasks])
