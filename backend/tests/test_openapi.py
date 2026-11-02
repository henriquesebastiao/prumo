"""The committed `openapi/openapi.json` is the contract with the Android app. It must match the
code; regenerate it with `make openapi`."""

import re
from pathlib import Path

from prumo.openapi import build_schema, render_schema

SNAPSHOT = Path(__file__).resolve().parents[2] / "openapi" / "openapi.json"


def test_snapshot_is_up_to_date() -> None:
    assert SNAPSHOT.exists(), "openapi/openapi.json is missing: run `make openapi`"
    assert SNAPSHOT.read_text(encoding="utf-8") == render_schema(build_schema()), (
        "openapi/openapi.json is out of date: run `make openapi` and commit the result"
    )


def test_operation_ids_are_tag_and_function_name() -> None:
    schema = build_schema()
    operation_ids = [
        operation["operationId"] for path in schema["paths"].values() for operation in path.values()
    ]
    assert len(operation_ids) == len(set(operation_ids))
    for operation_id in operation_ids:
        assert re.fullmatch(r"[a-z]+_[a-z_]+", operation_id), operation_id
    assert {"auth_login", "users_read_me", "dashboard_read_dashboard", "system_health"} <= set(
        operation_ids
    )


def test_every_route_documents_the_standard_error_body() -> None:
    schema = build_schema()
    assert "HTTPValidationError" not in schema["components"]["schemas"]
    for path, operations in schema["paths"].items():
        for method, operation in operations.items():
            for status, response in operation["responses"].items():
                if status.startswith(("4", "5")) and path != "/api/health":
                    ref = response["content"]["application/json"]["schema"]["$ref"]
                    assert ref.endswith("/ErrorResponse"), (method, path, status)
