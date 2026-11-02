"""Export of the OpenAPI contract (`openapi/openapi.json`)."""

import json
from typing import Any

from prumo.main import create_app


def build_schema() -> dict[str, Any]:
    return create_app().openapi()


def render_schema(schema: dict[str, Any]) -> str:
    return json.dumps(schema, indent=2, ensure_ascii=False) + "\n"
