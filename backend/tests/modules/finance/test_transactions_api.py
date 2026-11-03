from typing import Any

from fastapi.testclient import TestClient

from tests.modules.finance.helpers import (
    BASE,
    add,
    category_id,
    create_account,
    create_card,
    expense,
    income,
)


def error(response: Any) -> dict[str, Any]:
    assert response.status_code == 422, response.text
    body: dict[str, Any] = response.json()["error"]
    return body


def test_combinations_by_kind(auth_client: TestClient) -> None:
    nubank = create_account(auth_client)
    inter = create_account(auth_client, name="Inter")
    card = create_card(auth_client)
    food = category_id(auth_client, "Alimentação")
    salary = category_id(auth_client, "Salário", "income")

    def post(**payload: Any) -> Any:
        base = {"amount_cents": 1000, "occurred_on": "2026-11-17", "description": "X"}
        return auth_client.post(f"{BASE}/transactions", json=base | payload)

    missing = error(post(kind="income", account_id=nubank["id"]))
    assert missing["code"] == "finance.invalid_combination"
    assert missing["details"] == {"kind": "income", "missing": ["category_id"], "unexpected": []}
    both = error(
        post(kind="expense", account_id=nubank["id"], credit_card_id=card["id"], category_id=food)
    )
    assert both["details"]["unexpected"] == ["account_id"]
    transfer = error(
        post(
            kind="transfer",
            account_id=nubank["id"],
            destination_account_id=inter["id"],
            category_id=food,
        )
    )
    assert transfer["details"]["unexpected"] == ["category_id"]
    no_description = error(
        post(kind="expense", account_id=nubank["id"], category_id=food, description="  ")
    )
    assert no_description["details"]["missing"] == ["description"]
    invoice = error(
        post(
            kind="expense",
            credit_card_id=card["id"],
            category_id=food,
            invoice_closing_on="2026-12-03",
        )
    )
    assert invoice["details"]["unexpected"] == ["invoice_closing_on"]
    mismatch = error(post(kind="income", account_id=nubank["id"], category_id=food))
    assert mismatch["code"] == "finance.category_kind_mismatch"
    same = error(
        post(kind="transfer", account_id=nubank["id"], destination_account_id=nubank["id"])
    )
    assert same["code"] == "finance.same_account"
    negative = error(
        post(kind="income", account_id=nubank["id"], category_id=salary, amount_cents=-5)
    )
    assert negative["code"] == "finance.invalid_amount"
    zero = error(post(kind="adjustment", account_id=nubank["id"], amount_cents=0))
    assert zero["code"] == "finance.invalid_amount"
    installments = error(
        post(kind="expense", account_id=nubank["id"], category_id=food, installments=3)
    )
    assert installments["code"] == "finance.installments_require_card"

    # Valid ones; transfers and adjustments need no description.
    assert post(kind="income", account_id=nubank["id"], category_id=salary).status_code == 201
    transfer_ok = post(
        kind="transfer",
        account_id=nubank["id"],
        destination_account_id=inter["id"],
        description="",
    )
    assert transfer_ok.status_code == 201
    assert transfer_ok.json()["destination_account"]["name"] == "Inter"
    adjustment = post(kind="adjustment", account_id=nubank["id"], amount_cents=-300)
    assert adjustment.status_code == 201


def test_read_returns_references(auth_client: TestClient) -> None:
    nubank = create_account(auth_client, color="violet")
    created = expense(
        auth_client,
        1850,
        account_id=nubank["id"],
        description="Padaria",
        occurred_time="08:10",
        notes="Pão e café",
    )
    body = auth_client.get(f"{BASE}/transactions/{created['id']}").json()
    assert body["occurred_time"] == "08:10:00"
    assert body["account"] == {
        "id": nubank["id"],
        "name": "Nubank",
        "kind": "checking",
        "color": "violet",
        "icon": "landmark",
    }
    assert body["category"]["name"] == "Alimentação"
    assert body["category"]["icon"] == "utensils"
    assert body["credit_card"] is None
    assert body["invoice_closing_on"] is None


def test_update_keeps_the_kind_and_recomputes_the_invoice(auth_client: TestClient) -> None:
    nubank = create_account(auth_client)
    card = create_card(auth_client)
    created = expense(auth_client, 6400, account_id=nubank["id"], occurred_time="20:00")
    path = f"{BASE}/transactions/{created['id']}"

    moved = auth_client.patch(
        path, json={"account_id": None, "credit_card_id": card["id"], "kind": "income"}
    )
    assert moved.status_code == 200
    body = moved.json()
    assert body["kind"] == "expense"
    assert body["credit_card"]["id"] == card["id"]
    assert body["invoice_closing_on"] == "2026-12-03"
    later = auth_client.patch(
        path, json={"occurred_on": "2026-12-03", "occurred_time": None, "amount_cents": 6430}
    ).json()
    assert later["invoice_closing_on"] == "2027-01-03"
    assert later["occurred_time"] is None
    assert later["amount_cents"] == 6430

    assert error(auth_client.patch(path, json={"invoice_closing_on": "2026-12-03"}))["details"][
        "unexpected"
    ] == ["invoice_closing_on"]
    assert auth_client.patch(path, json={"description": None}).status_code == 422
    both = error(auth_client.patch(path, json={"account_id": nubank["id"]}))
    assert both["code"] == "finance.invalid_combination"

    assert auth_client.delete(path).status_code == 204
    assert auth_client.get(path).status_code == 404


def test_list_order_filters_search_and_totals(auth_client: TestClient) -> None:
    nubank = create_account(auth_client)
    inter = create_account(auth_client, name="Inter")
    wallet = create_account(auth_client, name="Carteira", kind="cash")
    card = create_card(auth_client)
    income(auth_client, 380000, nubank["id"])
    income(
        auth_client,
        150000,
        inter["id"],
        category="Freelance",
        on="2026-11-12",
        description="Site institucional",
    )
    expense(
        auth_client,
        110000,
        account_id=inter["id"],
        category="Moradia",
        on="2026-11-10",
        description="Aluguel",
    )
    expense(auth_client, 21240, account_id=nubank["id"])
    expense(
        auth_client,
        4636,
        credit_card_id=card["id"],
        category="Combustível",
        description="Posto · CG 160",
        occurred_time="21:10",
    )
    expense(
        auth_client,
        1850,
        account_id=wallet["id"],
        on="2026-11-17",
        description="Padaria",
        occurred_time="08:10",
    )
    expense(auth_client, 3000, account_id=nubank["id"], on="2026-10-20", description="Feira")
    add(
        auth_client,
        kind="transfer",
        amount_cents=50000,
        occurred_on="2026-11-12",
        account_id=inter["id"],
        destination_account_id=nubank["id"],
    )

    def search(**params: Any) -> dict[str, Any]:
        response = auth_client.get(f"{BASE}/transactions", params=params)
        assert response.status_code == 200, response.text
        body: dict[str, Any] = response.json()
        return body

    november = search(**{"from": "2026-11-01", "to": "2026-11-30"})
    assert november["total"] == 7
    assert [item["description"] for item in november["items"]] == [
        "Padaria",
        "Posto · CG 160",  # same day: with time first
        "Supermercado",
        "",  # the transfer: same day, no time, recorded last
        "Site institucional",
        "Aluguel",
        "Salário",
    ]
    assert november["income_cents"] == 530000
    assert november["expense_cents"] == 110000 + 21240 + 4636 + 1850

    page = search(limit=2, offset=2)
    assert page["total"] == 8
    assert len(page["items"]) == 2
    assert page["income_cents"] == 530000  # totals cover the whole filter

    assert search(kind="income")["total"] == 2
    by_account = search(account_id=nubank["id"])
    assert by_account["total"] == 4  # destination of the transfer included
    assert search(credit_card_id=card["id"])["items"][0]["credit_card"]["name"] == "Nubank"
    assert search(category_id=category_id(auth_client, "Moradia"))["total"] == 1

    assert [i["description"] for i in search(q="padaria")["items"]] == ["Padaria"]
    assert [i["description"] for i in search(q="212,40")["items"]] == ["Supermercado"]
    assert [i["description"] for i in search(q="212")["items"]] == ["Supermercado"]
    assert [i["description"] for i in search(q="1.500")["items"]] == ["Site institucional"]
    assert search(q="100%")["total"] == 0
    assert [i["amount_cents"] for i in search(sort="amount", limit=1)["items"]] == [1850]
    assert auth_client.get(f"{BASE}/transactions", params={"sort": "x"}).status_code == 422


def test_card_installments(auth_client: TestClient) -> None:
    card = create_card(auth_client)
    first = expense(
        auth_client,
        10000,
        credit_card_id=card["id"],
        category="Compras",
        description="Fone",
        installments=3,
    )
    assert first["installment_number"] == 1
    assert first["installment_count"] == 3
    items = auth_client.get(
        f"{BASE}/transactions", params={"credit_card_id": card["id"], "sort": "occurred_on"}
    ).json()["items"]
    assert [(i["amount_cents"], i["occurred_on"], i["invoice_closing_on"]) for i in items] == [
        (3334, "2026-11-16", "2026-12-03"),
        (3333, "2026-12-16", "2027-01-03"),
        (3333, "2027-01-16", "2027-02-03"),
    ]
    assert {i["installment_group_id"] for i in items} == {first["installment_group_id"]}
    card_now = auth_client.get(f"{BASE}/credit-cards/{card['id']}").json()
    assert card_now["available_limit_cents"] == 500000 - 10000  # F6: future installments too

    moved = auth_client.patch(
        f"{BASE}/transactions/{items[1]['id']}", json={"credit_card_id": None}
    )
    assert error(moved)["code"] == "finance.installments_require_card"
    assert auth_client.delete(f"{BASE}/transactions/{items[1]['id']}").status_code == 204
    assert (
        len(
            auth_client.get(f"{BASE}/transactions", params={"credit_card_id": card["id"]}).json()[
                "items"
            ]
        )
        == 2
    )
    removed = auth_client.delete(
        f"{BASE}/transactions/{first['id']}", params={"installments": "all"}
    )
    assert removed.status_code == 204
    assert auth_client.get(f"{BASE}/transactions").json()["total"] == 0


def test_other_user_gets_404(auth_client: TestClient, other_client: TestClient) -> None:
    nubank = create_account(auth_client)
    created = expense(auth_client, 1000, account_id=nubank["id"])
    path = f"{BASE}/transactions/{created['id']}"
    assert other_client.get(path).status_code == 404
    assert other_client.patch(path, json={"amount_cents": 1}).status_code == 404
    assert other_client.delete(path).status_code == 404
    assert other_client.get(f"{BASE}/transactions").json()["total"] == 0
    response = other_client.post(
        f"{BASE}/transactions",
        json={
            "kind": "adjustment",
            "amount_cents": 100,
            "occurred_on": "2026-11-17",
            "account_id": nubank["id"],
        },
    )
    assert response.status_code == 404
