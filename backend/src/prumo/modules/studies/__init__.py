"""Estudos: areas, subjects with their Obsidian note, topics, the weekly plan and the sessions."""

from prumo.core.modules import PrumoModule
from prumo.modules.studies.data_export import build_export
from prumo.modules.studies.router import router
from prumo.modules.studies.summary import build_activity, build_summary

module = PrumoModule(
    id="studies",
    version="0.1.0",
    router=router,
    summary=build_summary,
    activity=build_activity,
    export=build_export,
)
