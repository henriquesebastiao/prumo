"""The `PrumoModule` contract and the registry of installed modules.

The registry is filled once at startup from `prumo.modules.INSTALLED_MODULES` (see
`prumo.main.bootstrap`). From it the application mounts the routers, runs the user-creation hooks,
aggregates the dashboard and subscribes event handlers.
"""

import re
import typing
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from prumo.core.events import Event, EventHandler, bus
from prumo.core.export import ModuleExport

MODULE_ID = re.compile(r"^[a-z][a-z0-9_]{1,31}$")

# The user argument is the platform's `User` model; `core` cannot import it.
type SummaryProvider = Callable[[Session, Any], "ModuleSummary"]
type UserHook = Callable[[Session, Any], None]
type UpcomingProvider = Callable[[Session, Any], list["UpcomingItem"]]
type ActivityProvider = Callable[[Session, Any], list["ActivityItem"]]
type ExportProvider = Callable[[Session, Any], ModuleExport]

type EventValue = str | int | float | bool | None


class ModuleSummary(BaseModel):
    """Base of every dashboard summary. Subclasses narrow `module` to `Literal["<module id>"]`,
    which is the discriminator of the dashboard union."""

    module: str


class UpcomingItem(BaseModel):
    """Something due on a day ("Vem aí" on Início): an oil change, an invoice closing…"""

    module: str
    kind: str = Field(description="Stable code, translated by clients: `garage.oil_change`.")
    on: date
    subject: str = Field(description="What it is about, such as the vehicle name.")
    entity_id: UUID | None = None
    data: dict[str, EventValue] = Field(
        default_factory=dict, description="Values of the event, documented per `kind`."
    )


class ActivityItem(BaseModel):
    """A recent record ("Atividade recente" on Início)."""

    module: str
    kind: str = Field(description="Stable code, translated by clients: `garage.fueling`.")
    occurred_at: datetime
    subject: str
    entity_id: UUID | None = None
    data: dict[str, EventValue] = Field(default_factory=dict)


@dataclass(frozen=True)
class PrumoModule:
    id: str
    version: str
    router: APIRouter
    summary: SummaryProvider | None = None
    on_user_created: UserHook | None = None
    event_handlers: Mapping[type[Event], EventHandler] = field(default_factory=dict)
    upcoming: UpcomingProvider | None = None
    activity: ActivityProvider | None = None
    export: ExportProvider | None = None

    def __post_init__(self) -> None:
        if not MODULE_ID.match(self.id):
            msg = f"Invalid module id {self.id!r}: use lowercase letters, digits and underscores"
            raise ValueError(msg)
        if self.summary is not None:
            self.summary_schema  # noqa: B018 (validates the annotation early)

    @property
    def summary_schema(self) -> type[ModuleSummary] | None:
        """The summary schema, read from the return annotation of `summary`."""
        if self.summary is None:
            return None
        schema = typing.get_type_hints(self.summary).get("return")
        if not (isinstance(schema, type) and issubclass(schema, ModuleSummary)):
            msg = f"Module {self.id!r}: summary must be annotated to return a ModuleSummary"
            raise TypeError(msg)
        discriminator = schema.model_fields["module"].annotation
        if typing.get_origin(discriminator) is not Literal or typing.get_args(discriminator) != (
            self.id,
        ):
            msg = f"Module {self.id!r}: {schema.__name__}.module must be Literal[{self.id!r}]"
            raise TypeError(msg)
        return schema


class ModuleRegistry:
    def __init__(self) -> None:
        self._modules: tuple[PrumoModule, ...] = ()

    def install(self, modules: Sequence[PrumoModule]) -> None:
        ids = [module.id for module in modules]
        duplicates = sorted({module_id for module_id in ids if ids.count(module_id) > 1})
        if duplicates:
            msg = f"Duplicate module ids: {', '.join(duplicates)}"
            raise ValueError(msg)
        self._modules = tuple(modules)
        bus.reset()
        for module in self._modules:
            for event_type, handler in module.event_handlers.items():
                bus.subscribe(event_type, handler, module_id=module.id)

    @property
    def modules(self) -> tuple[PrumoModule, ...]:
        """Installed modules, in installation order (the default order for new users)."""
        return self._modules

    @property
    def ids(self) -> tuple[str, ...]:
        return tuple(module.id for module in self._modules)

    def get(self, module_id: str) -> PrumoModule | None:
        return next((module for module in self._modules if module.id == module_id), None)


registry = ModuleRegistry()
