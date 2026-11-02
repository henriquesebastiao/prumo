"""In-process event bus used for integrations between modules.

- Events are immutable dataclasses defined in the publishing module's public `events.py`.
- Publishing is synchronous and runs inside the caller's transaction: if a handler raises, the
  exception propagates and the whole operation is rolled back.
- Handlers only run when their module is enabled for the event's user (a user preference). The
  check is injected by the application (`EventBus.configure`), because `core` cannot read
  preferences itself.
"""

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session


@dataclass(frozen=True, kw_only=True)
class Event:
    user_id: UUID


type EventHandler = Callable[[Session, Any], None]
type ModuleEnabledCheck = Callable[[Session, UUID, str], bool]


def _always_enabled(session: Session, user_id: UUID, module_id: str) -> bool:
    return True


class EventBus:
    def __init__(self) -> None:
        self._subscriptions: defaultdict[type[Event], list[tuple[str, EventHandler]]] = defaultdict(
            list
        )
        self._is_enabled: ModuleEnabledCheck = _always_enabled

    def configure(self, is_enabled: ModuleEnabledCheck) -> None:
        self._is_enabled = is_enabled

    def reset(self) -> None:
        self._subscriptions.clear()
        self._is_enabled = _always_enabled

    def subscribe(self, event_type: type[Event], handler: EventHandler, *, module_id: str) -> None:
        self._subscriptions[event_type].append((module_id, handler))

    def handlers_for(self, event_type: type[Event]) -> list[tuple[str, EventHandler]]:
        return list(self._subscriptions.get(event_type, ()))

    def publish(self, session: Session, event: Event) -> None:
        for module_id, handler in self.handlers_for(type(event)):
            if self._is_enabled(session, event.user_id, module_id):
                handler(session, event)


bus = EventBus()


def publish(session: Session, event: Event) -> None:
    bus.publish(session, event)
