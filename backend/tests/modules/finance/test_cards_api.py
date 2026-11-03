from typing import Any

from fastapi.testclient import TestClient

from tests.modules.finance.helpers import BASE, add, create_account, create_card, expense


def pay(client: TestClient, card_id: str, closing_on: str, **payload: Any) -> Any:
    return client.post(
        f"{BASE}/credit-cards/{card_id}/invoices/{closing_on}/payments", json=payload
    )


def test_card_limit_and_current_invoice(auth_client: TestClient) -> None:
    nubank = create_account(auth_client)
    card = create_card(auth_client, payment_account_id=nubank["id"], color="green")
    assert card["payment_account"]["name"] == "Nubank"
    assert card["available_limit_cents"] == 500000
    assert card["current_invoice"] == {
        "closing_on": "2026-12-03",
        "due_on": "2026-12-10",
        "starts_on": "2026-11-03",
        "ends_on": "2026-12-02",
        "amount_cents": 0,
        "paid_cents": 0,
        "remaining_cents": 0,
        "status": "open",
        "transactions_count": 0,
        "last_payment_on": None,
        "last_payment_account": None,
    }

    expense(auth_client, 4636, credit_card_id=card["id"], category="Combustível")
    # F4: a purchase on the closing day goes to the next invoice.
    on_closing = expense(auth_client, 14431, credit_card_id=card["id"], on="2026-11-03")
    assert on_closing["invoice_closing_on"] == "2026-12-03"
    before = expense(auth_client, 193218, credit_card_id=card["id"], on="2026-11-02")
    assert before["invoice_closing_on"] == "2026-11-03"

    body = auth_client.get(f"{BASE}/credit-cards/{card['id']}").json()
    assert body["used_cents"] == 4636 + 14431 + 193218
    assert body["available_limit_cents"] == 500000 - body["used_cents"]
    assert body["current_invoice"]["amount_cents"] == 4636 + 14431
    assert body["current_invoice"]["transactions_count"] == 2
    assert body["transactions_count"] == 3


def test_invoices_payments_and_status(auth_client: TestClient) -> None:
    nubank = create_account(auth_client)
    card = create_card(auth_client)
    expense(auth_client, 193218, credit_card_id=card["id"], on="2026-10-20")
    expense(auth_client, 4636, credit_card_id=card["id"])

    invoices = auth_client.get(f"{BASE}/credit-cards/{card['id']}/invoices").json()["items"]
    assert [(i["closing_on"], i["status"]) for i in invoices] == [
        ("2026-12-03", "open"),
        ("2026-11-03", "overdue"),  # due 10/11, unpaid on 17/11
    ]

    partial = pay(
        auth_client, card["id"], "2026-11-03", amount_cents=100000, account_id=nubank["id"]
    )
    assert partial.status_code == 201
    assert partial.json()["kind"] == "card_payment"
    assert partial.json()["invoice_closing_on"] == "2026-11-03"
    detail = auth_client.get(f"{BASE}/credit-cards/{card['id']}/invoices/2026-11-03").json()
    assert detail["status"] == "overdue"
    assert detail["remaining_cents"] == 93218
    assert detail["card"]["id"] == card["id"]
    assert [t["amount_cents"] for t in detail["transactions"]] == [193218]
    assert [p["amount_cents"] for p in detail["payments"]] == [100000]

    pay(
        auth_client,
        card["id"],
        "2026-11-03",
        amount_cents=93218,
        account_id=nubank["id"],
        occurred_on="2026-11-10",
    )
    paid = auth_client.get(f"{BASE}/credit-cards/{card['id']}/invoices/2026-11-03").json()
    assert paid["status"] == "paid"
    assert paid["paid_cents"] == 193218
    assert paid["last_payment_on"] == "2026-11-17"  # the latest payment by date
    assert paid["last_payment_account"]["name"] == "Nubank"
    card_now = auth_client.get(f"{BASE}/credit-cards/{card['id']}").json()
    assert card_now["available_limit_cents"] == 500000 - 4636


def test_invalid_invoices(auth_client: TestClient) -> None:
    nubank = create_account(auth_client)
    card = create_card(auth_client)
    path = f"{BASE}/credit-cards/{card['id']}/invoices/2026-11-05"
    assert auth_client.get(path).status_code == 404
    assert (
        pay(
            auth_client, card["id"], "2026-11-05", amount_cents=1, account_id=nubank["id"]
        ).status_code
        == 404
    )
    response = auth_client.post(
        f"{BASE}/transactions",
        json={
            "kind": "card_payment",
            "amount_cents": 100,
            "occurred_on": "2026-11-17",
            "account_id": nubank["id"],
            "credit_card_id": card["id"],
            "invoice_closing_on": "2026-11-05",
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "finance.invalid_invoice"
    # Through the generic endpoint, a valid invoice is accepted.
    paid = add(
        auth_client,
        kind="card_payment",
        amount_cents=100,
        occurred_on="2026-11-17",
        account_id=nubank["id"],
        credit_card_id=card["id"],
        invoice_closing_on="2026-12-03",
    )
    assert paid["credit_card"]["id"] == card["id"]


def test_closing_day_change_keeps_existing_invoices(auth_client: TestClient) -> None:
    card = create_card(auth_client)
    expense(auth_client, 1000, credit_card_id=card["id"])
    updated = auth_client.patch(f"{BASE}/credit-cards/{card['id']}", json={"closing_day": 25})
    assert updated.status_code == 200
    assert updated.json()["current_invoice"]["closing_on"] == "2026-11-25"
    closings = [
        i["closing_on"]
        for i in auth_client.get(f"{BASE}/credit-cards/{card['id']}/invoices").json()["items"]
    ]
    assert closings == ["2026-12-03", "2026-11-25"]
    assert (
        auth_client.get(f"{BASE}/credit-cards/{card['id']}/invoices/2026-12-03").status_code == 200
    )


def test_card_with_transactions_can_only_be_archived(auth_client: TestClient) -> None:
    used = create_card(auth_client)
    unused = create_card(auth_client, name="Inter")
    expense(auth_client, 1000, credit_card_id=used["id"])
    response = auth_client.delete(f"{BASE}/credit-cards/{used['id']}")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "finance.card_in_use"
    assert auth_client.delete(f"{BASE}/credit-cards/{unused['id']}").status_code == 204
    assert auth_client.post(f"{BASE}/credit-cards/{used['id']}/archive").status_code == 200
    assert auth_client.get(f"{BASE}/credit-cards").json()["items"] == []
    archived = auth_client.get(f"{BASE}/credit-cards", params={"archived": "all"}).json()
    assert [card["name"] for card in archived["items"]] == ["Nubank"]
    restored = auth_client.post(f"{BASE}/credit-cards/{used['id']}/unarchive").json()
    assert restored["archived_at"] is None


def test_card_validation(auth_client: TestClient) -> None:
    response = auth_client.post(
        f"{BASE}/credit-cards",
        json={"name": "X", "limit_cents": -1, "closing_day": 0, "due_day": 32},
    )
    assert response.status_code == 422
    paths = {field["path"] for field in response.json()["error"]["fields"]}
    assert paths == {"limit_cents", "closing_day", "due_day"}


def test_other_user_gets_404(auth_client: TestClient, other_client: TestClient) -> None:
    card = create_card(auth_client)
    path = f"{BASE}/credit-cards/{card['id']}"
    assert other_client.get(path).status_code == 404
    assert other_client.patch(path, json={"name": "X"}).status_code == 404
    assert other_client.delete(path).status_code == 404
    assert other_client.post(f"{path}/archive").status_code == 404
    assert other_client.get(f"{path}/invoices").status_code == 404
    assert other_client.get(f"{path}/invoices/2026-12-03").status_code == 404
    account = create_account(other_client)
    assert (
        pay(
            other_client, card["id"], "2026-12-03", amount_cents=1, account_id=account["id"]
        ).status_code
        == 404
    )
    mine = create_account(auth_client)
    foreign_account = pay(
        auth_client, card["id"], "2026-12-03", amount_cents=1, account_id=account["id"]
    )
    assert foreign_account.status_code == 404
    assert mine["id"] != account["id"]
