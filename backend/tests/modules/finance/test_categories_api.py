from fastapi.testclient import TestClient

from tests.modules.finance.helpers import BASE, category_id, create_account, expense


def test_new_users_get_the_default_categories(auth_client: TestClient) -> None:
    body = auth_client.get(f"{BASE}/categories").json()
    assert body["month"] == "2026-11"
    expenses = [item["name"] for item in body["items"] if item["kind"] == "expense"]
    incomes = [item["name"] for item in body["items"] if item["kind"] == "income"]
    assert expenses == [
        "Alimentação",
        "Moradia",
        "Transporte",
        "Combustível",
        "Saúde",
        "Educação",
        "Lazer",
        "Compras",
        "Assinaturas",
        "Outros",
    ]
    assert incomes == ["Salário", "Freelance", "Rendimentos", "Outros"]
    fuel = next(item for item in body["items"] if item["name"] == "Combustível")
    assert (fuel["icon"], fuel["color"]) == ("fuel", "gray")


def test_month_counts_and_totals(auth_client: TestClient) -> None:
    account = create_account(auth_client)
    expense(auth_client, 21240, account_id=account["id"])
    expense(auth_client, 1850, account_id=account["id"], on="2026-11-17")
    expense(auth_client, 9999, account_id=account["id"], on="2026-11-30")  # after today
    expense(auth_client, 3000, account_id=account["id"], on="2026-10-20")

    def food(month: str | None = None) -> dict[str, int]:
        params = {"kind": "expense"} | ({"month": month} if month else {})
        items = auth_client.get(f"{BASE}/categories", params=params).json()["items"]
        found: dict[str, int] = next(item for item in items if item["name"] == "Alimentação")
        return found

    november = food()
    assert november["month_transactions_count"] == 2
    assert november["month_total_cents"] == 23090
    assert november["transactions_count"] == 4
    october = food("2026-10")
    assert october["month_transactions_count"] == 1
    assert october["month_total_cents"] == 3000
    assert auth_client.get(f"{BASE}/categories", params={"month": "2026-13"}).status_code == 422


def test_create_update_and_name_conflict(auth_client: TestClient) -> None:
    response = auth_client.post(
        f"{BASE}/categories", json={"kind": "expense", "name": " alimentação "}
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "finance.category_exists"
    # The same name is fine for the other kind ("Outros" exists in both).
    pets = auth_client.post(
        f"{BASE}/categories",
        json={"kind": "expense", "name": "Pets", "icon": "paw-print", "color": "amber"},
    )
    assert pets.status_code == 201
    assert pets.json()["transactions_count"] == 0
    pets_id = pets.json()["id"]
    clash = auth_client.patch(f"{BASE}/categories/{pets_id}", json={"name": "Lazer"})
    assert clash.status_code == 409
    renamed = auth_client.patch(f"{BASE}/categories/{pets_id}", json={"name": "Animais"})
    assert renamed.json()["name"] == "Animais"
    # Kind can change while unused.
    moved = auth_client.patch(f"{BASE}/categories/{pets_id}", json={"kind": "income"})
    assert moved.json()["kind"] == "income"


def test_used_category_keeps_its_kind_and_can_only_be_archived(auth_client: TestClient) -> None:
    account = create_account(auth_client)
    food = category_id(auth_client, "Alimentação")
    expense(auth_client, 1000, account_id=account["id"])

    kind = auth_client.patch(f"{BASE}/categories/{food}", json={"kind": "income"})
    assert kind.status_code == 422
    assert kind.json()["error"]["code"] == "finance.category_in_use"
    response = auth_client.delete(f"{BASE}/categories/{food}")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "finance.category_in_use"

    assert auth_client.post(f"{BASE}/categories/{food}/archive").status_code == 200
    names = [item["name"] for item in auth_client.get(f"{BASE}/categories").json()["items"]]
    assert "Alimentação" not in names
    archived = auth_client.get(f"{BASE}/categories", params={"archived": "true"}).json()["items"]
    assert [item["name"] for item in archived] == ["Alimentação"]
    # Archived categories still show up in reports.
    overview = auth_client.get(f"{BASE}/overview").json()
    assert overview["expenses_by_category"][0]["category"]["name"] == "Alimentação"
    unarchived = auth_client.post(f"{BASE}/categories/{food}/unarchive")
    assert unarchived.json()["archived_at"] is None

    unused = category_id(auth_client, "Educação")
    assert auth_client.delete(f"{BASE}/categories/{unused}").status_code == 204


def test_other_user_gets_404(auth_client: TestClient, other_client: TestClient) -> None:
    food = category_id(auth_client, "Alimentação")
    path = f"{BASE}/categories/{food}"
    assert other_client.get(path).status_code == 404
    assert other_client.patch(path, json={"name": "X"}).status_code == 404
    assert other_client.delete(path).status_code == 404
    assert other_client.post(f"{path}/archive").status_code == 404
    account = create_account(other_client)
    response = other_client.post(
        f"{BASE}/transactions",
        json={
            "kind": "expense",
            "amount_cents": 100,
            "occurred_on": "2026-11-17",
            "description": "X",
            "account_id": account["id"],
            "category_id": food,
        },
    )
    assert response.status_code == 404
