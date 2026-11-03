from uuid import uuid4, uuid7

from fastapi.testclient import TestClient

VEHICLE = {
    "kind": "car",
    "name": "Strada",
    "brand": "Fiat",
    "model": "Strada",
    "year": 2021,
    "current_km": 52300,
}


def test_repeating_a_post_returns_the_record(auth_client: TestClient) -> None:
    record_id = str(uuid7())
    first = auth_client.post("/api/v1/garage/vehicles", json=VEHICLE | {"id": record_id})
    assert first.status_code == 201
    assert first.json()["id"] == record_id
    again = auth_client.post(
        "/api/v1/garage/vehicles", json=VEHICLE | {"id": record_id, "name": "Outro nome"}
    )
    assert again.status_code == 200
    assert again.json()["name"] == "Strada"  # the body is not compared nor applied
    assert auth_client.get("/api/v1/garage/vehicles").json()["total"] == 1
    # The vehicle kept a single odometer reading (nothing was recorded twice).
    readings = auth_client.get(f"/api/v1/garage/vehicles/{record_id}/odometer").json()
    assert readings["total"] == 1


def test_id_rules(auth_client: TestClient, other_client: TestClient) -> None:
    record_id = str(uuid7())
    assert (
        auth_client.post("/api/v1/garage/vehicles", json=VEHICLE | {"id": record_id}).status_code
        == 201
    )
    taken = other_client.post("/api/v1/garage/vehicles", json=VEHICLE | {"id": record_id})
    assert taken.status_code == 409
    assert taken.json()["error"]["code"] == "id_conflict"
    v4 = auth_client.post("/api/v1/garage/vehicles", json=VEHICLE | {"id": str(uuid4())})
    assert v4.status_code == 422
    assert v4.json()["error"]["fields"][0]["path"] == "id"


def test_every_module_accepts_client_ids(auth_client: TestClient) -> None:
    account_id, payment_id, purchase_id = str(uuid7()), str(uuid7()), str(uuid7())
    account = {"id": account_id, "name": "Nubank", "kind": "checking"}
    assert auth_client.post("/api/v1/finance/accounts", json=account).status_code == 201
    assert auth_client.post("/api/v1/finance/accounts", json=account).status_code == 200
    card = auth_client.post(
        "/api/v1/finance/credit-cards",
        json={"name": "Nubank", "limit_cents": 100000, "closing_day": 3, "due_day": 10},
    ).json()
    categories = auth_client.get("/api/v1/finance/categories", params={"kind": "expense"})
    food = categories.json()["items"][0]["id"]
    purchase = {
        "id": purchase_id,
        "kind": "expense",
        "amount_cents": 9000,
        "occurred_on": "2026-11-17",
        "description": "Fone",
        "credit_card_id": card["id"],
        "category_id": food,
        "installments": 3,
    }
    created = auth_client.post("/api/v1/finance/transactions", json=purchase)
    assert created.status_code == 201
    assert created.json()["id"] == purchase_id  # the first installment
    assert auth_client.post("/api/v1/finance/transactions", json=purchase).status_code == 200
    assert auth_client.get("/api/v1/finance/transactions").json()["total"] == 3
    payment = {"id": payment_id, "amount_cents": 3000, "account_id": account_id}
    path = f"/api/v1/finance/credit-cards/{card['id']}/invoices/2026-12-03/payments"
    assert auth_client.post(path, json=payment).status_code == 201
    assert auth_client.post(path, json=payment).status_code == 200
    invoice = auth_client.get(f"/api/v1/finance/credit-cards/{card['id']}/invoices/2026-12-03")
    assert invoice.json()["paid_cents"] == 3000

    book_id, progress_id, note_id = str(uuid7()), str(uuid7()), str(uuid7())
    book = {"id": book_id, "title": "Código Limpo", "author": "R. C. Martin", "total_pages": 425}
    assert auth_client.post("/api/v1/reading/books", json=book).status_code == 201
    progress = {"id": progress_id, "page": 50}
    path = f"/api/v1/reading/books/{book_id}/progress"
    assert auth_client.post(path, json=progress).status_code == 201
    replay = auth_client.post(path, json=progress | {"page": 80})
    assert replay.status_code == 200
    assert replay.json()["current_page"] == 50
    history = auth_client.get(f"{path}").json()["items"]
    assert [item["id"] for item in history] == [progress_id]
    note = {"id": note_id, "content": "Nota"}
    notes = f"/api/v1/reading/books/{book_id}/notes"
    assert auth_client.post(notes, json=note).status_code == 201
    assert auth_client.post(notes, json=note).status_code == 200
    assert len(auth_client.get(notes).json()["items"]) == 1
