"""Veículos: vehicles, odometer, maintenances, oil changes, fuelings and workshops."""

from prumo.core.modules import PrumoModule
from prumo.modules.garage.data_export import build_export
from prumo.modules.garage.router import router
from prumo.modules.garage.summary import build_activity, build_summary, build_upcoming

module = PrumoModule(
    id="garage",
    version="0.1.0",
    router=router,
    summary=build_summary,
    upcoming=build_upcoming,
    activity=build_activity,
    export=build_export,
)
