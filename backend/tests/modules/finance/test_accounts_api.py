from fastapi.testclient import TestClient

from tests.modules.finance.helpers import (
    BASE,
    add,
    balance,
    create_account,
    create_card,
    expense,
    income,
)


def test_create_account_defaults(auth_client: TestClient) -> None:
    account = create_account(auth_client, kind="savings", initial_balance_cents=-500)
    assert account["icon"] == "vault"
    assert account["color"] == "green"
    assert account["include_in_total"] is True
    assert account["balance_cents"] == -500
    assert account["last_transaction_on"] is None
    assert account["transactions_count"] == 0


def test_account_validation(auth_client: TestClient) -> None:
    response = auth_client.post(
        f"{BASE}/accounts", json={"name": "", "kind": "bank", "color": "black", "icon": "No Icon"}
    )
    assert response.status_code == 422
    paths = {field["path"] for field in response.json()["error"]["fields"]}
    assert {"name", "kind", "color", "icon"} <= paths


def test_balance_follows_every_kind_of_transaction(auth_client: TestClient) -> None:
    nubank = create_account(auth_client)
    inter = create_account(auth_client, name="Inter", initial_balance_cents=50000)
    card = create_card(auth_client, payment_account_id=nubank["id"])

    income(auth_client, 380000, nubank["id"])
    assert balance(auth_client, nubank["id"]) == 480000
    expense(auth_client, 21240, account_id=nubank["id"])
    assert balance(auth_client, nubank["id"]) == 458760
    # F1: transactions after today do not change today's balance.
    expense(auth_client, 5000, account_id=nubank["id"], on="2026-11-25", description="Agendada")
    assert balance(auth_client, nubank["id"]) == 458760
    add(
        auth_client,
        kind="transfer",
        amount_cents=50000,
        occurred_on="2026-11-12",
        account_id=inter["id"],
        destination_account_id=nubank["id"],
    )
    assert balance(auth_client, nubank["id"]) == 508760
    assert balance(auth_client, inter["id"]) == 0
    # Card purchases only touch the account when the invoice is paid.
    expense(auth_client, 4636, credit_card_id=card["id"], category="Combustível")
    assert balance(auth_client, nubank["id"]) == 508760
    response = auth_client.post(
        f"{BASE}/credit-cards/{card['id']}/invoices/2026-12-03/payments",
        json={"amount_cents": 4636, "account_id": nubank["id"], "occurred_on": "2026-11-17"},
    )
    assert response.status_code == 201
    assert balance(auth_client, nubank["id"]) == 504124

    account = auth_client.get(f"{BASE}/accounts/{nubank['id']}").json()
    assert account["last_transaction_on"] == "2026-11-17"
    assert account["month_transactions_count"] == 4  # the scheduled one is not counted yet
    assert account["transactions_count"] == 5


def test_adjustment_records_the_difference(auth_client: TestClient) -> None:
    nubank = create_account(auth_client)
    expense(auth_client, 21240, account_id=nubank["id"])

    response = auth_client.post(
        f"{BASE}/accounts/{nubank['id']}/adjustments", json={"balance_cents": 80000}
    )
    assert response.status_code == 201
    adjustment = response.json()
    assert adjustment["kind"] == "adjustment"
    assert adjustment["amount_cents"] == 80000 - 78760
    assert adjustment["occurred_on"] == "2026-11-17"
    assert balance(auth_client, nubank["id"]) == 80000

    down = auth_client.post(
        f"{BASE}/accounts/{nubank['id']}/adjustments", json={"balance_cents": 70000}
    )
    assert down.json()["amount_cents"] == -10000
    same = auth_client.post(
        f"{BASE}/accounts/{nubank['id']}/adjustments", json={"balance_cents": 70000}
    )
    assert same.status_code == 422
    assert same.json()["error"]["code"] == "finance.balance_unchanged"

    # F3: adjustments are neither income nor expenses.
    overview = auth_client.get(f"{BASE}/overview").json()
    assert overview["income_cents"] == 0
    assert overview["expense_cents"] == 21240


def test_list_total_and_archive(auth_client: TestClient) -> None:
    nubank = create_account(auth_client, initial_balance_cents=481237)
    create_account(auth_client, name="Inter", initial_balance_cents=215690)
    create_account(
        auth_client, name="Reserva", initial_balance_cents=1000000, include_in_total=False
    )
    old = create_account(auth_client, name="Antiga", initial_balance_cents=999)

    archived = auth_client.post(f"{BASE}/accounts/{old['id']}/archive")
    assert archived.status_code == 200
    assert archived.json()["archived_at"] is not None

    body = auth_client.get(f"{BASE}/accounts").json()
    assert [item["name"] for item in body["items"]] == ["Nubank", "Inter", "Reserva"]
    assert body["total_balance_cents"] == 481237 + 215690
    only_archived = auth_client.get(f"{BASE}/accounts", params={"archived": "true"}).json()
    assert [item["name"] for item in only_archived["items"]] == ["Antiga"]
    assert only_archived["total_balance_cents"] == body["total_balance_cents"]

    auth_client.post(f"{BASE}/accounts/{old['id']}/unarchive")
    assert len(auth_client.get(f"{BASE}/accounts").json()["items"]) == 4

    updated = auth_client.patch(
        f"{BASE}/accounts/{nubank['id']}", json={"name": "Nu", "color": "violet"}
    )
    assert updated.json()["name"] == "Nu"
    assert updated.json()["color"] == "violet"
    assert (
        auth_client.patch(f"{BASE}/accounts/{nubank['id']}", json={"name": None}).status_code == 422
    )


def test_account_with_transactions_cannot_be_deleted(auth_client: TestClient) -> None:
    used = create_account(auth_client)
    unused = create_account(auth_client, name="Vazia")
    card = create_card(auth_client, payment_account_id=unused["id"])
    expense(auth_client, 1000, account_id=used["id"])

    response = auth_client.delete(f"{BASE}/accounts/{used['id']}")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "finance.account_in_use"
    assert response.json()["error"]["details"] == {"transactions_count": 1}

    assert auth_client.delete(f"{BASE}/accounts/{unused['id']}").status_code == 204
    assert auth_client.get(f"{BASE}/credit-cards/{card['id']}").json()["payment_account"] is None


def test_other_user_gets_404(auth_client: TestClient, other_client: TestClient) -> None:
    account = create_account(auth_client)
    path = f"{BASE}/accounts/{account['id']}"
    assert other_client.get(path).status_code == 404
    assert other_client.patch(path, json={"name": "X"}).status_code == 404
    assert other_client.delete(path).status_code == 404
    assert other_client.post(f"{path}/archive").status_code == 404
    assert other_client.post(f"{path}/adjustments", json={"balance_cents": 1}).status_code == 404
    assert other_client.get(f"{BASE}/accounts").json()["items"] == []
    # Nor can it be referenced by another user's records.
    response = other_client.post(
        f"{BASE}/credit-cards",
        json={
            "name": "X",
            "limit_cents": 1,
            "closing_day": 1,
            "due_day": 8,
            "payment_account_id": account["id"],
        },
    )
    assert response.status_code == 404
