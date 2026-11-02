from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from prumo.core.modules import registry
from prumo.system.preferences.service import get_preferences
from prumo.system.users.models import User
from tests import factories
from tests.conftest import AppFactory
from tests.fakes.modules import notes, plain, tasks

URL = "/api/v1/me/preferences"


def test_defaults(auth_client: TestClient) -> None:
    body = auth_client.get(URL).json()
    assert body["theme"] == "system"
    assert body["locale"] == "pt-BR"
    assert body["timezone"] == "America/Sao_Paulo"
    assert body["currency"] == "BRL"
    assert body["enabled_modules"] == list(registry.ids)


def test_partial_update(auth_client: TestClient) -> None:
    response = auth_client.patch(URL, json={"theme": "dark", "timezone": "America/Manaus"})
    assert response.status_code == 200
    body = response.json()
    assert body["theme"] == "dark"
    assert body["timezone"] == "America/Manaus"
    assert body["currency"] == "BRL"
    assert auth_client.get(URL).json()["theme"] == "dark"


def test_validation(auth_client: TestClient) -> None:
    cases = [
        ({"theme": "sepia"}, "theme", "enum"),
        ({"locale": "en-US"}, "locale", "literal_error"),
        ({"timezone": "Mars/Olympus"}, "timezone", "invalid_timezone"),
        ({"currency": "real"}, "currency", "string_pattern_mismatch"),
        ({"theme": None}, "theme", "not_nullable"),
        ({"enabled_modules": ["ghost"]}, "enabled_modules", "unknown_module"),
    ]
    for payload, path, code in cases:
        response = auth_client.patch(URL, json=payload)
        assert response.status_code == 422, payload
        field = response.json()["error"]["fields"][0]
        assert (field["path"], field["code"]) == (path, code), payload


def test_preferences_are_per_user(auth_client: TestClient, other_client: TestClient) -> None:
    auth_client.patch(URL, json={"theme": "dark"})
    assert other_client.get(URL).json()["theme"] == "system"


def _client_for(app: FastAPI, db: Session, user: User) -> TestClient:
    client = TestClient(app, base_url="https://testserver")
    client.headers["Authorization"] = f"Bearer {factories.create_session_token(db, user)}"
    return client


def test_module_order_and_enabled_state(make_app: AppFactory, db: Session) -> None:
    app = make_app([tasks, notes, plain])
    user = factories.create_user(db)
    client = _client_for(app, db, user)

    response = client.patch(URL, json={"enabled_modules": ["notes", "tasks"]})
    assert response.json()["enabled_modules"] == ["notes", "tasks"]
    modules = client.get("/api/v1/modules").json()["items"]
    assert [(m["id"], m["enabled"], m["position"]) for m in modules] == [
        ("notes", True, 0),
        ("tasks", True, 1),
        ("plain", False, 2),
    ]

    duplicate = client.patch(URL, json={"enabled_modules": ["notes", "notes"]})
    assert duplicate.status_code == 422
    assert duplicate.json()["error"]["fields"][0]["code"] == "duplicate_items"


def test_module_installed_later_is_enabled_at_the_end(make_app: AppFactory, db: Session) -> None:
    make_app([tasks])
    user = factories.create_user(db)
    assert get_preferences(db, user.id).module_order == ["tasks"]

    app = make_app([notes, tasks])  # `notes` installed after the user was created
    client = _client_for(app, db, user)
    assert client.get(URL).json()["enabled_modules"] == ["tasks", "notes"]
