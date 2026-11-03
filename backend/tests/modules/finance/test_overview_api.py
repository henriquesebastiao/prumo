from typing import Any

from fastapi.testclient import TestClient

from tests.modules.finance.helpers import (
    BASE,
    create_account,
    create_card,
    expense,
    income,
)


def seed(client: TestClient) -> dict[str, Any]:
    nubank = create_account(client, initial_balance_cents=100000)
    inter = create_account(client, name="Inter", initial_balance_cents=200000)
    create_account(client, name="Reserva", initial_balance_cents=50000, include_in_total=False)
    card = create_card(client)
    income(client, 380000, nubank["id"])
    income(client, 150000, inter["id"], category="Freelance", on="2026-11-12")
    expense(client, 110000, account_id=inter["id"], category="Moradia", on="2026-11-10")
    expense(client, 21240, account_id=nubank["id"], occurred_time="11:25")
    expense(client, 4636, credit_card_id=card["id"], category="Combustível", description="Posto")
    expense(client, 9999, account_id=nubank["id"], on="2026-11-25", description="Agendada")
    expense(client, 5000, account_id=nubank["id"], on="2026-10-20", description="Feira")
    expense(client, 7000, account_id=nubank["id"], on="2026-05-31", description="Fora")
    return {"nubank": nubank, "inter": inter, "card": card}


def test_overview_of_the_current_month(auth_client: TestClient) -> None:
    seed(auth_client)
    body = auth_client.get(f"{BASE}/overview").json()
    assert body["month"] == "2026-11"
    assert body["until"] == "2026-11-17"
    # Balances today: the scheduled expense is not counted.
    nubank = 100000 + 380000 - 21240 - 5000 - 7000
    inter = 200000 + 150000 - 110000
    assert [(a["account"]["name"], a["balance_cents"]) for a in body["accounts"]] == [
        ("Nubank", nubank),
        ("Inter", inter),
        ("Reserva", 50000),
    ]
    assert body["total_balance_cents"] == nubank + inter
    assert body["accounts_count"] == 2
    assert body["income_cents"] == 530000
    assert body["expense_cents"] == 110000 + 21240 + 4636  # card purchases by competence
    assert body["expense_percent"] == 26
    assert body["result_cents"] == 530000 - 135876
    assert [
        (s["category"]["name"], s["amount_cents"], s["percent"])
        for s in body["expenses_by_category"]
    ] == [("Moradia", 110000, 81), ("Alimentação", 21240, 16), ("Combustível", 4636, 3)]
    assert [s["category"]["name"] for s in body["income_by_category"]] == ["Salário", "Freelance"]
    assert [p["month"] for p in body["series"]] == [
        "2026-06",
        "2026-07",
        "2026-08",
        "2026-09",
        "2026-10",
        "2026-11",
    ]
    assert body["series"][-2] == {"month": "2026-10", "income_cents": 0, "expense_cents": 5000}
    assert body["series"][-1]["expense_cents"] == 135876
    [invoice] = body["open_invoices"]
    assert invoice["card"]["name"] == "Nubank"
    assert invoice["available_limit_cents"] == 500000 - 4636
    assert invoice["invoice"]["closing_on"] == "2026-12-03"
    assert invoice["invoice"]["amount_cents"] == 4636


def test_overview_of_another_month(auth_client: TestClient) -> None:
    seed(auth_client)
    october = auth_client.get(f"{BASE}/overview", params={"month": "2026-10"}).json()
    assert october["until"] == "2026-10-31"
    assert october["income_cents"] == 0
    assert october["expense_cents"] == 5000
    assert october["expense_percent"] is None
    assert october["accounts"][0]["balance_cents"] == 100000 - 5000 - 7000
    assert october["series"][0]["month"] == "2026-05"
    assert october["series"][0]["expense_cents"] == 7000
    december = auth_client.get(f"{BASE}/overview", params={"month": "2026-12"}).json()
    assert december["until"] == "2026-12-31"
    assert december["accounts"][0]["balance_cents"] == 100000 + 380000 - 21240 - 5000 - 7000 - 9999
    assert auth_client.get(f"{BASE}/overview", params={"month": "2026-1"}).status_code == 422


def test_dashboard_summary_upcoming_and_activity(auth_client: TestClient) -> None:
    seed(auth_client)
    body = auth_client.get("/api/v1/dashboard").json()
    summary = next(m for m in body["modules"] if m["module"] == "finance")
    assert summary["month"] == "2026-11"
    assert summary["income_cents"] == 530000
    assert summary["expense_percent"] == 26
    assert summary["expenses_by_category"][0]["category"]["name"] == "Moradia"
    assert summary["next_invoice"]["invoice"]["due_on"] == "2026-12-10"

    finance_upcoming = [i for i in body["upcoming"] if i["module"] == "finance"]
    assert [(i["kind"], i["on"]) for i in finance_upcoming] == [
        ("finance.invoice_closing", "2026-12-03"),
        ("finance.invoice_due", "2026-12-10"),
    ]
    assert finance_upcoming[0]["data"]["available_limit_cents"] == 500000 - 4636
    assert finance_upcoming[1]["data"]["status"] == "open"

    activity = [i for i in body["activity"] if i["module"] == "finance"]
    assert "Agendada" not in [i["subject"] for i in activity]
    supermarket = next(i for i in activity if i["subject"] == "Supermercado")
    assert supermarket["occurred_at"].startswith("2026-11-16T11:25:00")
    assert supermarket["data"] == {
        "transaction_kind": "expense",
        "amount_cents": 21240,
        "category": "Alimentação",
        "account": "Nubank",
        "destination_account": None,
        "credit_card": None,
        "occurred_time": "11:25",
    }


def test_paid_invoices_leave_upcoming(auth_client: TestClient) -> None:
    accounts = seed(auth_client)
    card, nubank = accounts["card"], accounts["nubank"]
    auth_client.post(
        f"{BASE}/credit-cards/{card['id']}/invoices/2026-12-03/payments",
        json={"amount_cents": 4636, "account_id": nubank["id"]},
    )
    body = auth_client.get("/api/v1/dashboard").json()
    assert [i for i in body["upcoming"] if i["module"] == "finance"] == []
    assert auth_client.get(f"{BASE}/overview").json()["open_invoices"] == []
