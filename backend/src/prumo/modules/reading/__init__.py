"""Livros: books, reading progress, notes and covers."""

from prumo.core.modules import PrumoModule
from prumo.modules.reading.router import router
from prumo.modules.reading.summary import build_activity, build_summary

module = PrumoModule(
    id="reading",
    version="0.1.0",
    router=router,
    summary=build_summary,
    activity=build_activity,
)
