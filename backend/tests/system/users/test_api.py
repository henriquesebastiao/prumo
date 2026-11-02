from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from prumo.core.security import verify_password
from prumo.system.auth.models import UserSession
from prumo.system.users.models import User
from tests import factories


def test_me_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "auth.required"


def test_read_me(auth_client: TestClient, user: User) -> None:
    response = auth_client.get("/api/v1/me")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(user.id)
    assert body["username"] == "ana"
    assert body["display_name"] == "Ana Souza"
    assert body["is_admin"] is False
    assert {"created_at", "updated_at"} <= body.keys()
    assert "password_hash" not in body


def test_update_display_name(auth_client: TestClient) -> None:
    response = auth_client.patch("/api/v1/me", json={"display_name": "  Ana S.  "})
    assert response.status_code == 200
    assert response.json()["display_name"] == "Ana S."


def test_update_me_validation(auth_client: TestClient) -> None:
    for payload, code in (
        ({"display_name": ""}, "string_too_short"),
        ({"display_name": None}, "not_nullable"),
    ):
        response = auth_client.patch("/api/v1/me", json=payload)
        assert response.status_code == 422
        assert response.json()["error"]["fields"][0] == {
            "path": "display_name",
            "code": code,
            "message": response.json()["error"]["fields"][0]["message"],
        }


def test_absent_field_is_left_unchanged(auth_client: TestClient) -> None:
    response = auth_client.patch("/api/v1/me", json={})
    assert response.status_code == 200
    assert response.json()["display_name"] == "Ana Souza"


def test_me_is_isolated_per_user(auth_client: TestClient, other_client: TestClient) -> None:
    assert auth_client.get("/api/v1/me").json()["username"] == "ana"
    assert other_client.get("/api/v1/me").json()["username"] == "bruno"


def test_change_password_revokes_other_sessions(
    auth_client: TestClient, db: Session, user: User
) -> None:
    other_session, other_token = factories.create_session(db, user, device_name="Notebook")
    response = auth_client.put(
        "/api/v1/me/password",
        json={"current_password": factories.DEFAULT_PASSWORD, "new_password": "outra-senha-789"},
    )
    assert response.status_code == 204
    db.refresh(user)
    assert verify_password(user.password_hash, "outra-senha-789")
    db.refresh(other_session)
    assert other_session.revoked_at is not None
    assert auth_client.get("/api/v1/me").status_code == 200  # current session stays
    revoked = auth_client.get("/api/v1/me", headers={"Authorization": f"Bearer {other_token}"})
    assert revoked.status_code == 401


def test_change_password_requires_the_current_one(auth_client: TestClient, db: Session) -> None:
    response = auth_client.put(
        "/api/v1/me/password",
        json={"current_password": "errada", "new_password": "outra-senha-789"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "auth.wrong_password"
    assert db.query(UserSession).filter(UserSession.revoked_at.is_not(None)).count() == 0


def test_change_password_validates_new_password(auth_client: TestClient) -> None:
    response = auth_client.put(
        "/api/v1/me/password",
        json={"current_password": factories.DEFAULT_PASSWORD, "new_password": "curta"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["fields"][0]["path"] == "new_password"
