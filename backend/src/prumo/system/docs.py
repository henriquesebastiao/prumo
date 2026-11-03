"""Interactive API documentation (`/api/docs`), served without any CDN.

The Swagger UI files live in `prumo/static/swagger-ui/` (copied by
`scripts/update-swagger-ui.sh`), so a self-hosted instance works offline.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

SWAGGER_UI = Path(__file__).resolve().parents[1] / "static" / "swagger-ui"
STATIC = "/api/docs/static"


def install_docs(app: FastAPI) -> None:
    app.mount(STATIC, StaticFiles(directory=SWAGGER_UI), name="swagger-ui")

    @app.get("/api/docs", include_in_schema=False, tags=["docs"])
    def swagger_ui() -> HTMLResponse:
        return get_swagger_ui_html(
            openapi_url=app.openapi_url or "/api/openapi.json",
            title=f"{app.title} · docs",
            swagger_js_url=f"{STATIC}/swagger-ui-bundle.js",
            swagger_css_url=f"{STATIC}/swagger-ui.css",
            swagger_favicon_url=f"{STATIC}/favicon-32x32.png",
        )
