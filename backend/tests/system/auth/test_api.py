from datetime import timedelta

import time_machine
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from prumo.core.clock import utcnow
from prumo.system.auth.models import SessionClient, UserSession
from prumo.system.users.models import User
from tests import factories

LOGIN = "/api/v1/auth/login"
WEB = {"X-Prumo-Client": "web"}


def login_payload(**overrides: object) -> dict[str, object]:
    return {"username": "ana", "password": factories.DEFAULT_PASSWORD, "client": "web"} | overrides


# ---------------------------------------------------------------- web (cookie)


def test_web_login_sets_http_only_cookie_and_returns_no_token(
    client: TestClient, user: User
) -> None:
    response = client.post(
        LOGIN, json=login_payload(), headers={"User-Agent": "Mozilla/5.0 (X11; Linux) Firefox/150"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["user"]["username"] == "ana"
    assert body["token"] is None
    cookie = response.headers["set-cookie"]
    assert cookie.startswith("prumo_session=")
    for attribute in ("HttpOnly", "Path=/api", "SameSite=lax", "Secure", "Max-Age=2592000"):
        assert attribute in cookie
    assert client.get("/api/v1/me").json()["username"] == "ana"
    sessions = client.get("/api/v1/auth/sessions").json()["items"]
    assert sessions[0]["device_name"] == "Firefox · Linux"
    assert sessions[0]["client"] == "web"


def test_web_login_without_remember_uses_a_browser_session_cookie(
    client: TestClient, user: User, db: Session
) -> None:
    response = client.post(LOGIN, json=login_payload(remember=False))
    assert response.status_code == 200
    assert "Max-Age" not in response.headers["set-cookie"]
    user_session = db.scalars(select(UserSession)).one()
    assert user_session.expires_at - user_session.created_at <= timedelta(hours=12, seconds=1)


def test_cookie_mutations_require_the_client_header(client: TestClient, user: User) -> None:
    client.post(LOGIN, json=login_payload())
    response = client.patch("/api/v1/me", json={"display_name": "Ana"})
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "auth.client_header_required"
    response = client.patch("/api/v1/me", json={"display_name": "Ana"}, headers=WEB)
    assert response.status_code == 200


def test_logout_revokes_session_and_clears_cookie(client: TestClient, user: User) -> None:
    client.post(LOGIN, json=login_payload())
    response = client.post("/api/v1/auth/logout", headers=WEB)
    assert response.status_code == 204
    assert 'prumo_session=""' in response.headers["set-cookie"]
    assert client.get("/api/v1/me").status_code == 401


# ---------------------------------------------------------------- app (bearer)


def test_app_login_returns_bearer_token(client: TestClient, user: User) -> None:
    response = client.post(
        LOGIN, json=login_payload(client="app", device_name="Pixel 8", remember=False)
    )
    assert response.status_code == 200
    body = response.json()
    assert "set-cookie" not in response.headers
    assert body["token"]
    me = client.get("/api/v1/me", headers={"Authorization": f"Bearer {body['token']}"})
    assert me.status_code == 200
    sessions = client.get(
        "/api/v1/auth/sessions", headers={"Authorization": f"Bearer {body['token']}"}
    ).json()["items"]
    assert sessions[0]["device_name"] == "Pixel 8"
    assert sessions[0]["current"] is True
    # App sessions are long-lived regardless of `remember`.
    assert body["expires_at"] > (utcnow() + timedelta(days=179)).isoformat()


def test_bearer_mutations_do_not_need_the_client_header(auth_client: TestClient) -> None:
    response = auth_client.patch("/api/v1/me", json={"display_name": "Ana"})
    assert response.status_code == 200


def test_invalid_bearer_token(client: TestClient) -> None:
    response = client.get("/api/v1/me", headers={"Authorization": "Bearer nope"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "auth.required"


def test_expired_session(client: TestClient, db: Session, user: User) -> None:
    token = factories.create_session_token(db, user, expires_in=timedelta(minutes=5))
    with time_machine.travel(utcnow() + timedelta(minutes=6)):
        response = client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "auth.session_expired"


def test_last_used_at_is_refreshed_at_most_once_a_minute(
    client: TestClient, db: Session, user: User
) -> None:
    user_session, token = factories.create_session(db, user)
    first = user_session.last_used_at
    headers = {"Authorization": f"Bearer {token}"}
    client.get("/api/v1/me", headers=headers)
    db.refresh(user_session)
    assert user_session.last_used_at == first
    with time_machine.travel(utcnow() + timedelta(minutes=2)):
        client.get("/api/v1/me", headers=headers)
    db.refresh(user_session)
    assert user_session.last_used_at > first


# ---------------------------------------------------------------- credentials and rate limit


def test_wrong_password_and_unknown_user_look_the_same(client: TestClient, user: User) -> None:
    wrong = client.post(LOGIN, json=login_payload(password="errada"))
    unknown = client.post(LOGIN, json=login_payload(username="ninguem"))
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()
    assert wrong.json()["error"]["code"] == "auth.invalid_credentials"


def test_username_is_case_insensitive_on_login(client: TestClient, user: User) -> None:
    assert client.post(LOGIN, json=login_payload(username=" ANA ")).status_code == 200


def test_five_failures_lock_the_username_and_ip_for_fifteen_minutes(
    client: TestClient, user: User
) -> None:
    start = utcnow()
    with time_machine.travel(start, tick=False):
        for _ in range(5):
            assert client.post(LOGIN, json=login_payload(password="errada")).status_code == 401
        locked = client.post(LOGIN, json=login_payload())
    assert locked.status_code == 429
    assert locked.json()["error"]["code"] == "auth.rate_limited"
    assert locked.headers["Retry-After"] == "900"

    with time_machine.travel(start + timedelta(minutes=14), tick=False):
        assert client.post(LOGIN, json=login_payload()).status_code == 429
    with time_machine.travel(start + timedelta(minutes=15, seconds=1), tick=False):
        assert client.post(LOGIN, json=login_payload()).status_code == 200


def test_a_successful_login_resets_the_failure_count(client: TestClient, user: User) -> None:
    for _ in range(4):
        client.post(LOGIN, json=login_payload(password="errada"))
    assert client.post(LOGIN, json=login_payload()).status_code == 200
    for _ in range(4):
        client.post(LOGIN, json=login_payload(password="errada"))
    assert client.post(LOGIN, json=login_payload()).status_code == 200


def test_failures_spread_over_more_than_the_window_do_not_lock(
    client: TestClient, user: User
) -> None:
    start = utcnow()
    for minute in (0, 4, 8, 12, 16):
        with time_machine.travel(start + timedelta(minutes=minute), tick=False):
            client.post(LOGIN, json=login_payload(password="errada"))
    with time_machine.travel(start + timedelta(minutes=16, seconds=10), tick=False):
        assert client.post(LOGIN, json=login_payload()).status_code == 200


def test_login_validation(client: TestClient) -> None:
    response = client.post(LOGIN, json={"username": "ana", "password": "x", "client": "tv"})
    assert response.status_code == 422
    assert response.json()["error"]["fields"][0]["path"] == "client"


# ---------------------------------------------------------------- session management


def test_list_sessions_marks_the_current_one(
    auth_client: TestClient, db: Session, user: User, other_user: User
) -> None:
    factories.create_session(db, user, client=SessionClient.WEB, device_name="Firefox · Linux")
    factories.create_session(db, other_user)
    expired, _ = factories.create_session(db, user, expires_in=timedelta(seconds=-1))
    items = auth_client.get("/api/v1/auth/sessions").json()["items"]
    assert len(items) == 2
    assert sum(item["current"] for item in items) == 1
    assert str(expired.id) not in {item["id"] for item in items}


def test_revoke_another_session(auth_client: TestClient, db: Session, user: User) -> None:
    target, token = factories.create_session(db, user, device_name="Notebook")
    response = auth_client.delete(f"/api/v1/auth/sessions/{target.id}")
    assert response.status_code == 204
    assert (
        auth_client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"}).status_code
        == 401
    )
    assert auth_client.delete(f"/api/v1/auth/sessions/{target.id}").status_code == 404


def test_revoking_a_session_of_another_user_is_not_found(
    auth_client: TestClient, db: Session, other_user: User
) -> None:
    foreign, token = factories.create_session(db, other_user)
    response = auth_client.delete(f"/api/v1/auth/sessions/{foreign.id}")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
    me = auth_client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})
    assert me.json()["username"] == "bruno"


def test_session_endpoints_require_authentication(client: TestClient) -> None:
    assert client.get("/api/v1/auth/sessions").status_code == 401
    assert client.post("/api/v1/auth/logout").status_code == 401
