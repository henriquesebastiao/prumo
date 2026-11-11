"""Hábitos: habits to practice (check or quantity, with a versioned frequency and pauses) and to
quit (relapses and the time without)."""

from prumo.core.modules import PrumoModule
from prumo.modules.habits.data_export import build_export
from prumo.modules.habits.router import router
from prumo.modules.habits.summary import build_summary

module = PrumoModule(
    id="habits",
    version="0.1.0",
    router=router,
    summary=build_summary,
    export=build_export,
)
