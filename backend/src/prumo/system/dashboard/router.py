"""`GET /dashboard`. The response model is a discriminated union (on `module`) of the summary
schemas of the installed modules, so it is built when the application starts."""

from typing import Annotated, Any, Union

from fastapi import APIRouter
from pydantic import BaseModel, Field, create_model

from prumo.core.deps import SessionDep
from prumo.core.errors import error_responses
from prumo.core.modules import ActivityItem, ModuleRegistry, ModuleSummary, UpcomingItem
from prumo.system.auth.deps import CurrentUser
from prumo.system.dashboard.service import build_activity, build_dashboard, build_upcoming


def _summary_type(registry: ModuleRegistry) -> Any:
    schemas = [
        schema for module in registry.modules if (schema := module.summary_schema) is not None
    ]
    if not schemas:
        return ModuleSummary
    if len(schemas) == 1:
        return schemas[0]
    return Annotated[Union[tuple(schemas)], Field(discriminator="module")]  # noqa: UP007


def build_router(registry: ModuleRegistry) -> APIRouter:
    item = _summary_type(registry)
    fields: dict[str, Any] = {
        "modules": (
            list[item],  # type: ignore[valid-type]
            Field(description="Summaries of the enabled modules, in the user's order."),
        ),
        "upcoming": (
            list[UpcomingItem],
            Field(description="Due items of the enabled modules (next 60 days), by date."),
        ),
        "activity": (
            list[ActivityItem],
            Field(description="Recent records of the enabled modules, newest first."),
        ),
    }
    dashboard_model: type[BaseModel] = create_model("DashboardRead", **fields)
    router = APIRouter(tags=["dashboard"], responses=error_responses(401))

    @router.get("/dashboard", response_model=dashboard_model)
    def read_dashboard(session: SessionDep, user: CurrentUser) -> Any:
        """Home screen data: the summary of each enabled module."""
        return {
            "modules": build_dashboard(session, user),
            "upcoming": build_upcoming(session, user),
            "activity": build_activity(session, user),
        }

    return router
