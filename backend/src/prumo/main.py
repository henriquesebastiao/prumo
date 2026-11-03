"""Application factory. Run with `uvicorn prumo.main:create_app --factory`."""

from collections.abc import Sequence

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute

from prumo import __version__
from prumo.core.config import get_settings
from prumo.core.errors import document_standard_errors, install_error_handlers
from prumo.core.events import bus
from prumo.core.modules import PrumoModule, registry
from prumo.modules import INSTALLED_MODULES
from prumo.system import health
from prumo.system.auth.deps import CLIENT_HEADER
from prumo.system.auth.router import router as auth_router
from prumo.system.dashboard.router import build_router as build_dashboard_router
from prumo.system.docs import install_docs
from prumo.system.export.router import router as export_router
from prumo.system.modules.router import router as modules_router
from prumo.system.preferences.router import router as preferences_router
from prumo.system.preferences.service import is_module_enabled
from prumo.system.sync.router import router as sync_router
from prumo.system.users.router import router as users_router

API_V1 = "/api/v1"


def operation_id(route: APIRoute) -> str:
    """Stable `operation_id`: `{tag}_{function name}`. Renaming a route function changes the
    contract."""
    if not route.tags:
        msg = f"Route {route.path} has no tag"
        raise ValueError(msg)
    return f"{route.tags[0]}_{route.name}"


def bootstrap(modules: Sequence[PrumoModule] | None = None) -> None:
    """Installs the modules into the registry and wires the event bus. Used by the API and the
    CLI."""
    registry.install(INSTALLED_MODULES if modules is None else modules)
    bus.configure(is_module_enabled)


def create_app(modules: Sequence[PrumoModule] | None = None) -> FastAPI:
    bootstrap(modules)
    settings = get_settings()
    app = FastAPI(
        title="Prumo API",
        version=__version__,
        description="API of Prumo. The web app and the Android app are clients of this contract.",
        openapi_url="/api/openapi.json",
        docs_url=None,
        redoc_url=None,
        generate_unique_id_function=operation_id,
    )
    install_error_handlers(app)
    document_standard_errors(app)
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["Authorization", "Content-Type", CLIENT_HEADER],
        )

    app.include_router(health.router, prefix="/api")
    install_docs(app)

    v1 = APIRouter(prefix=API_V1)
    v1.include_router(auth_router)
    v1.include_router(users_router)
    v1.include_router(export_router)
    v1.include_router(preferences_router)
    v1.include_router(modules_router)
    v1.include_router(build_dashboard_router(registry))
    v1.include_router(sync_router)
    for module in registry.modules:
        v1.include_router(module.router, prefix=f"/{module.id}", tags=[module.id])
    app.include_router(v1)
    return app
