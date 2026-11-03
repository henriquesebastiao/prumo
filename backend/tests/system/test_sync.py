from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from prumo.system.sync.models import SyncDeletion
from prumo.system.users.models import User

VEHICLE = {"kind": "car", "brand": "Fiat", "model": "Strada", "year": 2021, "current_km": 1000}


def now() -> str:
    return datetime.now(UTC).isoformat()


def test_lists_return_what_changed_since(auth_client: TestClient) -> None:
    first = auth_client.post("/api/v1/garage/vehicles", json=VEHICLE | {"name": "Antigo"}).json()
    second = auth_client.post("/api/v1/garage/vehicles", json=VEHICLE | {"name": "Outro"}).json()
    since = now()
    auth_client.patch(f"/api/v1/garage/vehicles/{second['id']}", json={"name": "Novo nome"})
    auth_client.post(f"/api/v1/garage/vehicles/{first['id']}/archive")
    third = auth_client.post("/api/v1/garage/vehicles", json=VEHICLE | {"name": "Recente"}).json()

    body = auth_client.get(
        "/api/v1/garage/vehicles", params={"updated_since": since, "sort": "-name"}
    ).json()
    # Archived ones included, oldest change first, `sort` ignored.
    assert [item["id"] for item in body["items"]] == [second["id"], first["id"], third["id"]]
    assert body["total"] == 3
    naive = since.replace("+00:00", "")
    assert (
        auth_client.get("/api/v1/garage/vehicles", params={"updated_since": naive}).json()["total"]
        == 3
    )
    later = auth_client.get("/api/v1/garage/vehicles", params={"updated_since": now()}).json()
    assert later["items"] == []


def test_other_lists_accept_updated_since(auth_client: TestClient) -> None:
    book = auth_client.post(
        "/api/v1/reading/books", json={"title": "Livro", "author": "Autor", "total_pages": 100}
    ).json()
    since = now()
    auth_client.post(f"/api/v1/reading/books/{book['id']}/notes", json={"content": "Nota"})
    account = auth_client.post(
        "/api/v1/finance/accounts", json={"name": "Conta", "kind": "cash"}
    ).json()
    auth_client.post(
        f"/api/v1/finance/accounts/{account['id']}/adjustments", json={"balance_cents": 500}
    )
    params = {"updated_since": since}
    assert auth_client.get("/api/v1/reading/notes", params=params).json()["total"] == 1
    assert auth_client.get("/api/v1/reading/books", params=params).json()["total"] == 0
    transactions = auth_client.get("/api/v1/finance/transactions", params=params).json()
    assert [item["kind"] for item in transactions["items"]] == ["adjustment"]
    for path in (
        "/api/v1/garage/maintenances",
        "/api/v1/garage/fuelings",
        "/api/v1/garage/workshops",
    ):
        assert auth_client.get(path, params=params).status_code == 200, path


def test_deletions_include_cascades(auth_client: TestClient, other_client: TestClient) -> None:
    since = now()
    book = auth_client.post(
        "/api/v1/reading/books", json={"title": "Livro", "author": "Autor", "total_pages": 100}
    ).json()
    auth_client.post(f"/api/v1/reading/books/{book['id']}/progress", json={"page": 10})
    note = auth_client.post(
        f"/api/v1/reading/books/{book['id']}/notes", json={"content": "Nota"}
    ).json()
    other = other_client.post(
        "/api/v1/reading/books", json={"title": "Dele", "author": "X", "total_pages": 10}
    ).json()
    auth_client.delete(f"/api/v1/reading/books/{book['id']}")
    other_client.delete(f"/api/v1/reading/books/{other['id']}")

    body = auth_client.get("/api/v1/sync/deletions", params={"since": since}).json()
    resources = {(item["resource"], item["id"]) for item in body["items"]}
    assert ("reading.books", book["id"]) in resources
    assert ("reading.notes", note["id"]) in resources
    assert any(resource == "reading.progress" for resource, _ in resources)
    assert ("reading.books", other["id"]) not in resources  # never another user's
    assert body["total"] == 3
    assert body["server_time"] >= since
    later = auth_client.get("/api/v1/sync/deletions", params={"since": body["server_time"]})
    assert later.json()["items"] == []


def test_bulk_deletes_are_recorded(auth_client: TestClient) -> None:
    card = auth_client.post(
        "/api/v1/finance/credit-cards",
        json={"name": "Cartão", "limit_cents": 100000, "closing_day": 3, "due_day": 10},
    ).json()
    category = auth_client.get("/api/v1/finance/categories", params={"kind": "expense"})
    purchase = auth_client.post(
        "/api/v1/finance/transactions",
        json={
            "kind": "expense",
            "amount_cents": 9000,
            "occurred_on": "2026-11-17",
            "description": "Fone",
            "credit_card_id": card["id"],
            "category_id": category.json()["items"][0]["id"],
            "installments": 3,
        },
    ).json()
    since = now()
    auth_client.delete(
        f"/api/v1/finance/transactions/{purchase['id']}", params={"installments": "all"}
    )
    body = auth_client.get("/api/v1/sync/deletions", params={"since": since}).json()
    assert [item["resource"] for item in body["items"]] == ["finance.transactions"] * 3


def test_old_cursors_and_deleted_users(auth_client: TestClient, db: Session, user: User) -> None:
    old = (datetime.now(UTC) - timedelta(days=181)).isoformat()
    response = auth_client.get("/api/v1/sync/deletions", params={"since": old})
    assert response.status_code == 410
    assert response.json()["error"]["code"] == "sync.since_too_old"
    assert auth_client.get("/api/v1/sync/deletions").status_code == 422

    auth_client.post("/api/v1/garage/vehicles", json=VEHICLE | {"name": "Carro"})
    db.execute(delete(User).where(User.id == user.id))
    recorded = db.scalar(
        select(func.count()).select_from(SyncDeletion).where(SyncDeletion.user_id == user.id)
    )
    assert recorded == 0  # deleting the user does not fill the log with its rows
