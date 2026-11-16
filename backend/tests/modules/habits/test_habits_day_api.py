"""The day of habits, the manual order, the time of day and the new recurrences (D48), through the
API, with the clock at Tuesday 17/11/2026 14:30 in São Paulo (conftest)."""

from typing import Any

import time_machine
from fastapi.testclient import TestClient

from tests.modules.habits.test_habits_api import BASE, code, create, mark


def names(items: list[dict[str, Any]]) -> list[str]:
    return [item["habit"]["name"] for item in items]


def test_the_day_is_grouped_and_ordered(auth_client: TestClient) -> None:
    devotional = create(auth_client, name="Devocional", time_of_day="05:15")
    create(auth_client, name="Regar plantas", time_of_day="18:00")
    create(auth_client, name="Meditar", time_of_day="07:00")
    create(auth_client, name="Anki")
    create(
        auth_client,
        name="Academia",
        started_on="2026-11-02",
        frequency={"kind": "per_period", "times": 3, "period": "week"},
    )
    create(
        auth_client,
        name="Tarefa do mês",
        frequency={"kind": "per_period", "times": 1, "period": "month", "preferred_day": 15},
    )
    create(
        auth_client,
        name="Correr",
        started_on="2026-11-16",
        frequency={"kind": "per_period", "times": 5, "period": "week"},
    )
    create(
        auth_client,
        name="Trocar roupa de cama",
        frequency={"kind": "weekdays", "weekdays": [5], "every_n_weeks": 2},
    )
    create(auth_client, name="Doce", kind="quit", started_on="2026-11-10")
    mark(auth_client, devotional["id"], "2026-11-17")

    day = auth_client.get(f"{BASE}/day").json()
    assert (day["on"], day["today"], day["now"]) == ("2026-11-17", "2026-11-17", "14:30")
    assert names(day["timeline"]) == ["Meditar", "Regar plantas"]
    assert [i["late"] for i in day["timeline"]] == [True, False]
    assert day["timeline"][0]["habit"]["time_of_day"] == "07:00"
    # Without a time, in the manual order (creation): the monthly one rose on its preferred day,
    # the weekly one with 5 times left in 6 days is due soon.
    assert names(day["untimed"]) == ["Anki", "Tarefa do mês", "Correr"]
    promoted = {i["habit"]["name"]: (i["promoted"], i["due_in_days"]) for i in day["untimed"]}
    assert promoted["Tarefa do mês"] == ("preferred_day", None)
    assert promoted["Correr"] == ("due_soon", 5)
    assert names(day["period"]) == ["Academia"]
    period = day["period"][0]["period"]
    assert period == {
        "period": "week",
        "starts_on": "2026-11-16",
        "ends_on": "2026-11-22",
        "done": 0,
        "target": 3,
        "days_left": 6,
        "neutral": False,
    }
    assert day["period"][0]["week"] == {"done": 0, "target": 3}
    assert names(day["done_items"]) == ["Devocional"]
    assert (day["done"], day["scheduled"]) == (1, 6)
    assert [q["name"] for q in day["quit"]] == ["Doce"]

    # A past day: no "now", the devotional open again, nothing late.
    yesterday = auth_client.get(f"{BASE}/day", params={"on": "2026-11-16"}).json()
    assert yesterday["now"] is None
    assert names(yesterday["timeline"]) == ["Devocional", "Meditar", "Regar plantas"]
    assert not any(i["late"] for i in yesterday["timeline"])
    tomorrow = auth_client.get(f"{BASE}/day", params={"on": "2026-11-18"})
    assert code(tomorrow) == "habits.future_date"

    # Início: the next open ones, in the order of the day.
    dashboard = auth_client.get("/api/v1/dashboard").json()
    summary = next(m for m in dashboard["modules"] if m["module"] == "habits")
    assert names(summary["upcoming"]) == [
        "Meditar",
        "Regar plantas",
        "Anki",
        "Tarefa do mês",
        "Correr",
    ]
    assert [p["name"] for p in summary["pending"]] == ["Meditar", "Regar plantas", "Anki"]
    assert (summary["done_today"], summary["scheduled_today"], summary["pending_more"]) == (1, 6, 2)

    # A period met on another day leaves the day.
    gym = next(i for i in day["period"] if i["habit"]["name"] == "Academia")["habit"]["id"]
    for on in ("2026-11-16", "2026-11-14"):
        assert auth_client.put(f"{BASE}/{gym}/entries/{on}", json={"value": 1}).status_code == 200
    mark(auth_client, gym, "2026-11-13")
    later = auth_client.get(f"{BASE}/day").json()
    # 13/11 and 14/11 belong to last week: this one has 1 of 3.
    assert next(i for i in later["period"] if i["habit"]["id"] == gym)["period"]["done"] == 1


def test_the_list_follows_the_time_and_the_manual_order(auth_client: TestClient) -> None:
    anki = create(auth_client, name="Anki")
    water = create(auth_client, name="Beber água")
    read = create(auth_client, name="Ler")
    run = create(auth_client, name="Correr", time_of_day="06:00")
    quit_habit = create(auth_client, name="Doce", kind="quit")
    assert [anki["position"], water["position"], read["position"]] == [0, 1, 2]

    def order() -> list[str]:
        return [h["name"] for h in auth_client.get(BASE).json()["items"]]

    assert order() == ["Correr", "Anki", "Beber água", "Ler", "Doce"]
    # Moving two of them: they swap their places; the others keep theirs.
    response = auth_client.put(f"{BASE}/order", json={"ids": [read["id"], anki["id"]]})
    assert response.status_code == 204
    assert order() == ["Correr", "Ler", "Beber água", "Anki", "Doce"]
    # Repeating is safe.
    auth_client.put(f"{BASE}/order", json={"ids": [read["id"], anki["id"]]})
    assert order() == ["Correr", "Ler", "Beber água", "Anki", "Doce"]
    auth_client.put(f"{BASE}/order", json={"ids": [quit_habit["id"], water["id"]]})
    assert order() == ["Correr", "Ler", "Doce", "Anki", "Beber água"]

    # The time can be cleared; the habit goes to its manual place.
    cleared = auth_client.patch(f"{BASE}/{run['id']}", json={"time_of_day": None})
    assert cleared.json()["time_of_day"] is None
    assert order() == ["Ler", "Doce", "Anki", "Correr", "Beber água"]
    timed = auth_client.patch(f"{BASE}/{anki['id']}", json={"time_of_day": "21:30"})
    assert timed.json()["time_of_day"] == "21:30"
    assert order()[0] == "Anki"

    repeated = auth_client.put(f"{BASE}/order", json={"ids": [anki["id"], anki["id"]]})
    assert code(repeated) == "validation_error"
    unknown = "019a9c00-0000-7000-8000-0000000000ff"
    assert auth_client.put(f"{BASE}/order", json={"ids": [unknown]}).status_code == 404


def test_frequencies_are_validated(auth_client: TestClient) -> None:
    def post(frequency: dict[str, Any], **fields: Any) -> Any:
        payload = {"name": "X", "kind": "build", "frequency": frequency} | fields
        return auth_client.post(BASE, json=payload)

    fortnight = {"kind": "per_period", "period": "fortnight"}
    assert code(post(fortnight | {"times": 15})) == "habits.times_exceed_period"
    assert post(fortnight | {"times": 14}).status_code == 201
    assert code(post({"kind": "per_period", "period": "month", "times": 29})) == "validation_error"
    week = {"kind": "per_period", "period": "week", "times": 2}
    assert code(post(week | {"times": 8})) == "habits.times_exceed_period"
    assert code(post(week | {"preferred_day": 9})) == "habits.preferred_day_mismatch"
    month = {"kind": "per_period", "period": "month", "times": 1}
    assert code(post(month | {"preferred_day": 0})) == "habits.preferred_day_mismatch"
    assert code(post({"kind": "weekdays", "weekdays": [5], "every_n_weeks": 0})) == (
        "validation_error"
    )
    assert code(post({"kind": "month_days", "month_days": [5], "every_n_months": 13})) == (
        "validation_error"
    )
    assert code(post({"kind": "month_days", "month_days": []})) == "validation_error"
    assert code(post({"kind": "month_weekday", "weekday": 6})) == "validation_error"
    assert code(post({"kind": "month_weekday", "week_of_month": 5, "weekday": 6})) == (
        "validation_error"
    )
    assert code(post({"kind": "daily"}, time_of_day="25:00")) == "validation_error"
    assert code(post({"kind": "daily"}, time_of_day="7:00")) == "validation_error"


def test_each_recurrence_reads_back_with_its_next_day(auth_client: TestClient) -> None:
    tank = create(
        auth_client,
        name="Limpar caixa d'água",
        started_on="2026-08-01",
        frequency={"kind": "month_days", "month_days": [5], "every_n_months": 3},
    )
    frequency = tank["frequency"]
    assert (frequency["kind"], frequency["month_days"], frequency["every_n_months"]) == (
        "month_days",
        [5],
        3,
    )
    assert (frequency["cadence"], frequency["month_last_day"], frequency["times"]) == (
        "longer",
        False,
        None,
    )
    assert tank["next_due"] == "2027-02-05"
    assert tank["streak_unit"] == "occurrence"
    assert tank["today"]["scheduled"] is False

    review = create(
        auth_client,
        name="Revisão mensal",
        frequency={"kind": "month_weekday", "week_of_month": 1, "weekday": 6},
    )
    assert review["frequency"]["cadence"] == "monthly"
    assert review["next_due"] == "2026-12-06"

    sheets = create(
        auth_client,
        name="Trocar roupa de cama",
        started_on="2026-11-07",
        frequency={"kind": "weekdays", "weekdays": [5], "every_n_weeks": 2},
    )
    assert sheets["frequency"]["every_n_weeks"] == 2
    assert sheets["frequency"]["cadence"] == "fortnightly"
    assert sheets["next_due"] == "2026-11-21"
    calendar = auth_client.get(f"{BASE}/{sheets['id']}/calendar").json()
    statuses = {d["on"]: d["status"] for d in calendar["days"]}
    assert (statuses["2026-11-07"], statuses["2026-11-14"]) == ("missed", "unscheduled")

    chore = create(
        auth_client,
        name="Tarefa do mês",
        frequency={"kind": "per_period", "times": 1, "period": "month", "preferred_day": 20},
    )
    assert chore["next_due"] == "2026-11-20"
    assert chore["streak_unit"] == "month"
    assert chore["week"] is None
    assert chore["period"]["ends_on"] == "2026-11-30"
    assert chore["frequency"]["times_per_week"] is None

    legacy = create(auth_client, name="Academia", frequency={"kind": "weekly", "times_per_week": 3})
    assert (legacy["frequency"]["kind"], legacy["frequency"]["times_per_week"]) == (
        "per_period",
        3,
    )


def test_today_follows_the_user_zone_near_midnight(auth_client: TestClient) -> None:
    habit = create(auth_client, name="Ler", time_of_day="23:00")
    # 23:50 of Tuesday in São Paulo is already Wednesday in UTC.
    with time_machine.travel("2026-11-18T02:50:00Z", tick=False):
        day = auth_client.get(f"{BASE}/day").json()
        assert (day["today"], day["now"]) == ("2026-11-17", "23:50")
        assert day["timeline"][0]["late"] is True
        assert code(auth_client.put(f"{BASE}/{habit['id']}/entries/2026-11-18", json={})) == (
            "habits.future_date"
        )
    with time_machine.travel("2026-11-18T03:10:00Z", tick=False):
        day = auth_client.get(f"{BASE}/day").json()
        assert (day["today"], day["now"]) == ("2026-11-18", "00:10")
        assert day["timeline"][0]["late"] is False
        assert (
            auth_client.put(f"{BASE}/{habit['id']}/entries/2026-11-18", json={}).status_code == 200
        )


def test_other_user_cannot_reorder(auth_client: TestClient, other_client: TestClient) -> None:
    habit = create(auth_client)
    assert other_client.put(f"{BASE}/order", json={"ids": [habit["id"]]}).status_code == 404
    assert other_client.get(f"{BASE}/day").json()["untimed"] == []
