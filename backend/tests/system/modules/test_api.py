import time_machine
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from prumo.main import create_app
from tests import factories
from tests.conftest import AppFactory
from tests.fakes.modules import notes, plain, tasks


def _client(make_app: AppFactory, db: Session) -> TestClient:
    app = make_app([tasks, notes, plain])
    user = factories.create_user(db)
    client = TestClient(app, base_url="https://testserver")
    client.headers["Authorization"] = f"Bearer {factories.create_session_token(db, user)}"
    return client


def test_installed_modules_in_default_order(make_app: AppFactory, db: Session) -> None:
    items = _client(make_app, db).get("/api/v1/modules").json()["items"]
    assert items == [
        {"id": "tasks", "version": "1.0.0", "enabled": True, "position": 0},
        {"id": "notes", "version": "0.3.0", "enabled": True, "position": 1},
        {"id": "plain", "version": "0.1.0", "enabled": True, "position": 2},
    ]


def test_module_router_is_mounted_under_its_id(make_app: AppFactory, db: Session) -> None:
    response = _client(make_app, db).get("/api/v1/tasks/ping")
    assert response.json() == {"module": "tasks", "user": "ana"}


def test_disabled_module_api_keeps_working(make_app: AppFactory, db: Session) -> None:
    client = _client(make_app, db)
    client.patch("/api/v1/me/preferences", json={"enabled_modules": ["notes"]})
    assert client.get("/api/v1/tasks/ping").status_code == 200


def test_dashboard_aggregates_enabled_modules_in_user_order(
    make_app: AppFactory, db: Session
) -> None:
    client = _client(make_app, db)
    assert client.get("/api/v1/dashboard").json()["modules"] == [
        {"module": "tasks", "open_tasks": 3},
        {"module": "notes", "latest": "Comprar pão"},
    ]
    client.patch("/api/v1/me/preferences", json={"enabled_modules": ["notes", "plain"]})
    body = client.get("/api/v1/dashboard").json()
    assert body["modules"] == [{"module": "notes", "latest": "Comprar pão"}]
    assert [item["module"] for item in body["upcoming"] + body["activity"]] == ["notes", "notes"]


@time_machine.travel("2026-11-17T15:00:00Z", tick=False)
def test_dashboard_merges_upcoming_and_activity(make_app: AppFactory, db: Session) -> None:
    body = _client(make_app, db).get("/api/v1/dashboard").json()
    # Sorted by date across modules; items beyond 60 days are left out.
    assert [(item["subject"], item["on"]) for item in body["upcoming"]] == [
        ("Ideias", "2026-11-18"),
        ("Relatório", "2026-11-20"),
    ]
    # Newest first.
    assert [item["subject"] for item in body["activity"]] == ["Comprar pão", "Pagar luz"]
    assert body["activity"][1]["data"] == {"points": 3}


def test_dashboard_schema_is_a_discriminated_union(make_app: AppFactory) -> None:
    schema = create_app([tasks, notes]).openapi()
    items = schema["components"]["schemas"]["DashboardRead"]["properties"]["modules"]["items"]
    assert items["discriminator"]["propertyName"] == "module"
    assert {ref["$ref"].rsplit("/", 1)[-1] for ref in items["oneOf"]} == {
        "TasksSummary",
        "NotesSummary",
    }


def test_dashboard_without_modules(make_app: AppFactory, db: Session) -> None:
    app = make_app([])
    user = factories.create_user(db)
    client = TestClient(app, base_url="https://testserver")
    client.headers["Authorization"] = f"Bearer {factories.create_session_token(db, user)}"
    body = client.get("/api/v1/dashboard").json()
    assert body == {"modules": [], "upcoming": [], "activity": []}


def test_modules_and_dashboard_require_authentication(client: TestClient) -> None:
    assert client.get("/api/v1/modules").status_code == 401
    assert client.get("/api/v1/dashboard").status_code == 401
