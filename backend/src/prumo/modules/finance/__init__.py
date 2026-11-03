"""Finanças: accounts, categories, transactions, credit cards and invoices."""

from prumo.core.modules import PrumoModule
from prumo.modules.finance import service
from prumo.modules.finance.data_export import build_export
from prumo.modules.finance.router import router
from prumo.modules.finance.summary import build_activity, build_summary, build_upcoming

module = PrumoModule(
    id="finance",
    version="0.1.0",
    router=router,
    summary=build_summary,
    on_user_created=service.create_default_categories,
    upcoming=build_upcoming,
    activity=build_activity,
    export=build_export,
)
