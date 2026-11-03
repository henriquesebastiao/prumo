"""Helpers that create finance records through the API, like a client would."""

from typing import Any

from fastapi.testclient import TestClient

BASE = "/api/v1/finance"


def created(client: TestClient, path: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = client.post(f"{BASE}{path}", json=payload)
    assert response.status_code == 201, response.text
    body: dict[str, Any] = response.json()
    return body


def create_account(client: TestClient, **overrides: Any) -> dict[str, Any]:
    payload = {"name": "Nubank", "kind": "checking", "initial_balance_cents": 100000}
    return created(client, "/accounts", payload | overrides)


def create_card(client: TestClient, **overrides: Any) -> dict[str, Any]:
    payload = {"name": "Nubank", "limit_cents": 500000, "closing_day": 3, "due_day": 10}
    return created(client, "/credit-cards", payload | overrides)


def category_id(client: TestClient, name: str, kind: str = "expense") -> str:
    items = client.get(f"{BASE}/categories", params={"kind": kind}).json()["items"]
    return next(str(item["id"]) for item in items if item["name"] == name)


def add(client: TestClient, **payload: Any) -> dict[str, Any]:
    return created(client, "/transactions", payload)


def expense(
    client: TestClient,
    amount: int,
    *,
    category: str = "Alimentação",
    on: str = "2026-11-16",
    description: str = "Supermercado",
    **extra: Any,
) -> dict[str, Any]:
    return add(
        client,
        kind="expense",
        amount_cents=amount,
        occurred_on=on,
        description=description,
        category_id=category_id(client, category),
        **extra,
    )


def income(
    client: TestClient,
    amount: int,
    account_id: str,
    *,
    category: str = "Salário",
    on: str = "2026-11-05",
    description: str = "Salário",
) -> dict[str, Any]:
    return add(
        client,
        kind="income",
        amount_cents=amount,
        occurred_on=on,
        description=description,
        account_id=account_id,
        category_id=category_id(client, category, "income"),
    )


def balance(client: TestClient, account_id: str) -> int:
    value: int = client.get(f"{BASE}/accounts/{account_id}").json()["balance_cents"]
    return value
