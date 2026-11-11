"""Hábitos through the API, with the clock at Tuesday 17/11/2026 14:30 in São Paulo (conftest)."""

from typing import Any

from fastapi.testclient import TestClient

BASE = "/api/v1/habits"


def create(client: TestClient, **fields: Any) -> dict[str, Any]:
    payload = {"name": "Ler a Bíblia", "kind": "build", "started_on": "2026-11-01"} | fields
    response = client.post(BASE, json=payload)
    assert response.status_code == 201, response.text
    body: dict[str, Any] = response.json()
    return body


def mark(client: TestClient, habit_id: str, on: str, value: int = 1) -> dict[str, Any]:
    response = client.put(f"{BASE}/{habit_id}/entries/{on}", json={"value": value})
    assert response.status_code == 200, response.text
    body: dict[str, Any] = response.json()
    return body


def code(response: Any) -> str:
    return str(response.json()["error"]["code"])


def test_create_list_edit_archive_and_delete(auth_client: TestClient) -> None:
    habit = create(auth_client)
    assert habit["measure"] == "check"
    assert habit["frequency"]["kind"] == "daily"
    assert habit["frequency"]["valid_from"] == "2026-11-01"
    assert habit["streak_unit"] == "day"
    assert habit["today"] == {"scheduled": True, "done": False, "value": None}
    assert habit["clean_days"] is None

    water = auth_client.post(BASE, json={"name": "Água", "kind": "build", "measure": "quantity"})
    assert code(water) == "habits.invalid_measure"
    future = auth_client.post(BASE, json={"name": "X", "kind": "quit", "started_on": "2026-11-18"})
    assert code(future) == "habits.future_date"

    renamed = auth_client.patch(f"{BASE}/{habit['id']}", json={"name": "Bíblia", "icon": "book"})
    assert (renamed.json()["name"], renamed.json()["icon"]) == ("Bíblia", "book")
    assert code(auth_client.patch(f"{BASE}/{habit['id']}", json={"target_value": 3})) == (
        "habits.invalid_measure"
    )
    # An earlier start takes the first frequency with it.
    earlier = auth_client.patch(f"{BASE}/{habit['id']}", json={"started_on": "2026-10-20"})
    assert earlier.json()["frequency"]["valid_from"] == "2026-10-20"

    assert auth_client.get(BASE).json()["total"] == 1
    auth_client.post(f"{BASE}/{habit['id']}/archive")
    assert auth_client.get(BASE).json()["total"] == 0
    assert auth_client.get(BASE, params={"archived": "all"}).json()["total"] == 1
    assert auth_client.get(f"{BASE}/today").json()["items"] == []
    auth_client.post(f"{BASE}/{habit['id']}/unarchive")
    assert auth_client.delete(f"{BASE}/{habit['id']}").status_code == 204
    assert auth_client.get(f"{BASE}/{habit['id']}").status_code == 404


def test_marking_days_is_idempotent_and_refuses_the_future(auth_client: TestClient) -> None:
    habit = create(auth_client)
    first = mark(auth_client, habit["id"], "2026-11-17", 5)
    assert first["today"] == {"scheduled": True, "done": True, "value": 1}
    again = mark(auth_client, habit["id"], "2026-11-17")
    assert again["current_streak"] == 1
    for day in ("2026-11-14", "2026-11-15", "2026-11-16"):
        mark(auth_client, habit["id"], day)
    assert auth_client.get(f"{BASE}/{habit['id']}").json()["current_streak"] == 4

    late = auth_client.put(f"{BASE}/{habit['id']}/entries/2026-11-18", json={"value": 1})
    assert code(late) == "habits.future_date"
    early = auth_client.put(f"{BASE}/{habit['id']}/entries/2026-10-31", json={"value": 1})
    assert code(early) == "habits.before_start"

    unmarked = auth_client.delete(f"{BASE}/{habit['id']}/entries/2026-11-17")
    assert unmarked.status_code == 200
    assert unmarked.json()["today"]["done"] is False
    # Today open does not break the streak.
    assert unmarked.json()["current_streak"] == 3
    assert auth_client.delete(f"{BASE}/{habit['id']}/entries/2026-11-17").status_code == 200

    entries = auth_client.get(f"{BASE}/entries", params={"habit_id": habit["id"]}).json()
    assert [e["on"] for e in entries["items"]] == ["2026-11-16", "2026-11-15", "2026-11-14"]


def test_a_quantity_is_partial_until_the_target(auth_client: TestClient) -> None:
    water = create(auth_client, name="Beber água", measure="quantity", target_value=2000, unit="ml")
    partial = mark(auth_client, water["id"], "2026-11-17", 1250)
    assert partial["today"] == {"scheduled": True, "done": False, "value": 1250}
    today = auth_client.get(f"{BASE}/today").json()
    item = today["items"][0]
    assert (item["value"], item["done"], item["settled"]) == (1250, False, False)
    assert item["habit"]["target_value"] == 2000
    calendar = auth_client.get(f"{BASE}/{water['id']}/calendar").json()
    assert calendar["month"] == "2026-11"
    assert calendar["next_month"] is None
    assert calendar["previous_month"] == "2026-10"
    day = next(d for d in calendar["days"] if d["on"] == "2026-11-17")
    assert (day["status"], day["value"]) == ("partial", 1250)
    assert next(d for d in calendar["days"] if d["on"] == "2026-11-16")["status"] == "missed"
    assert next(d for d in calendar["days"] if d["on"] == "2026-11-18")["status"] == "future"
    october = auth_client.get(f"{BASE}/{water['id']}/calendar", params={"month": "2026-10"})
    assert october.json()["next_month"] == "2026-11"
    assert {d["status"] for d in october.json()["days"]} == {"unscheduled"}
    assert (
        auth_client.get(f"{BASE}/{water['id']}/calendar", params={"month": "2026-13"}).status_code
        == 422
    )


def test_weekly_shows_the_week(auth_client: TestClient) -> None:
    gym = create(
        auth_client,
        name="Academia",
        started_on="2026-10-05",
        frequency={"kind": "weekly", "times_per_week": 3},
    )
    for day in ("2026-11-09", "2026-11-11", "2026-11-13", "2026-11-16"):
        mark(auth_client, gym["id"], day)
    read = auth_client.get(f"{BASE}/{gym['id']}").json()
    assert read["streak_unit"] == "week"
    assert read["week"] == {"done": 1, "target": 3}
    assert read["current_streak"] == 1
    item = auth_client.get(f"{BASE}/today").json()["items"][0]
    assert item["week"] == {"done": 1, "target": 3}
    assert item["settled"] is False


def test_frequency_versions(auth_client: TestClient) -> None:
    habit = create(auth_client, name="Anki")
    past = auth_client.post(
        f"{BASE}/{habit['id']}/frequencies", json={"valid_from": "2026-11-10", "kind": "daily"}
    )
    assert code(past) == "habits.frequency_locked"
    weekdays = {"valid_from": "2026-11-23", "kind": "weekdays", "weekdays": [4, 0, 2]}
    created = auth_client.post(f"{BASE}/{habit['id']}/frequencies", json=weekdays)
    assert created.status_code == 201, created.text
    assert created.json()["weekdays"] == [0, 2, 4]
    assert created.json()["state"] == "future"
    taken = auth_client.post(f"{BASE}/{habit['id']}/frequencies", json=weekdays)
    assert taken.status_code == 409
    assert code(taken) == "habits.frequency_date_taken"
    bad = auth_client.post(
        f"{BASE}/{habit['id']}/frequencies", json={"valid_from": "2026-11-30", "kind": "weekly"}
    )
    assert bad.status_code == 422

    detail = auth_client.get(f"{BASE}/{habit['id']}").json()
    assert [(f["valid_from"], f["state"]) for f in detail["frequencies"]] == [
        ("2026-11-23", "future"),
        ("2026-11-01", "current"),
    ]
    assert detail["frequencies"][1]["valid_until"] == "2026-11-22"
    first_id = detail["frequencies"][1]["id"]
    locked = auth_client.patch(
        f"{BASE}/frequencies/{first_id}", json={"kind": "weekly", "times_per_week": 2}
    )
    assert code(locked) == "habits.frequency_locked"
    changed = auth_client.patch(
        f"{BASE}/frequencies/{created.json()['id']}", json={"kind": "weekly", "times_per_week": 4}
    )
    assert (changed.json()["kind"], changed.json()["times_per_week"]) == ("weekly", 4)
    assert auth_client.delete(f"{BASE}/frequencies/{created.json()['id']}").status_code == 204
    assert code(auth_client.delete(f"{BASE}/frequencies/{first_id}")) == "habits.frequency_locked"


def test_pauses(auth_client: TestClient) -> None:
    habit = create(auth_client)
    pause = auth_client.post(
        f"{BASE}/{habit['id']}/pauses", json={"starts_on": "2026-11-05", "ends_on": "2026-11-09"}
    )
    assert pause.status_code == 201
    overlap = auth_client.post(f"{BASE}/{habit['id']}/pauses", json={"starts_on": "2026-11-09"})
    assert code(overlap) == "habits.pause_overlap"
    backwards = auth_client.post(
        f"{BASE}/{habit['id']}/pauses", json={"starts_on": "2026-11-12", "ends_on": "2026-11-11"}
    )
    assert backwards.status_code == 422
    open_pause = auth_client.post(f"{BASE}/{habit['id']}/pauses", json={"starts_on": "2026-11-16"})
    assert open_pause.json()["ends_on"] is None
    paused = auth_client.get(f"{BASE}/{habit['id']}").json()
    assert paused["paused"] is True
    assert paused["today"]["scheduled"] is False
    assert auth_client.get(f"{BASE}/today").json()["items"] == []
    calendar = auth_client.get(f"{BASE}/{habit['id']}/calendar").json()
    assert next(d for d in calendar["days"] if d["on"] == "2026-11-07")["status"] == "paused"

    ended = auth_client.patch(
        f"{BASE}/pauses/{open_pause.json()['id']}", json={"ends_on": "2026-11-16"}
    )
    assert ended.json()["ends_on"] == "2026-11-16"
    assert auth_client.get(f"{BASE}/{habit['id']}").json()["paused"] is False
    assert auth_client.delete(f"{BASE}/pauses/{pause.json()['id']}").status_code == 204
    assert len(auth_client.get(f"{BASE}/{habit['id']}").json()["pauses"]) == 1


def test_quitting_counts_the_time_without(auth_client: TestClient) -> None:
    habit = create(auth_client, name="Redes sociais à noite", kind="quit", started_on="2026-08-01")
    assert habit["measure"] is None
    assert habit["frequency"] is None
    assert habit["clean_since"] == "2026-08-01T03:00:00Z"
    assert habit["clean_days"] == 108
    relapse = auth_client.post(
        f"{BASE}/{habit['id']}/relapses",
        json={"occurred_at": "2026-11-08T23:30:00-03:00", "note": " domingo entediado "},
    )
    assert relapse.status_code == 201
    assert relapse.json()["clean_days"] == 8
    assert relapse.json()["relapses_30d"] == 1
    assert relapse.json()["best_clean_days"] == 99
    detail = auth_client.get(f"{BASE}/{habit['id']}").json()
    assert detail["relapses"][0]["note"] == "domingo entediado"
    future = auth_client.post(
        f"{BASE}/{habit['id']}/relapses", json={"occurred_at": "2026-11-18T10:00:00-03:00"}
    )
    assert code(future) == "habits.future_date"
    before = auth_client.post(
        f"{BASE}/{habit['id']}/relapses", json={"occurred_at": "2026-07-31T10:00:00-03:00"}
    )
    assert code(before) == "habits.before_start"
    assert code(auth_client.put(f"{BASE}/{habit['id']}/entries/2026-11-17", json={})) == (
        "habits.not_build"
    )
    assert code(auth_client.get(f"{BASE}/{habit['id']}/calendar")) == "habits.not_build"
    build = create(auth_client)
    no_relapse = auth_client.post(
        f"{BASE}/{build['id']}/relapses", json={"occurred_at": "2026-11-17T10:00:00Z"}
    )
    assert code(no_relapse) == "habits.not_quit"
    assert auth_client.delete(f"{BASE}/relapses/{detail['relapses'][0]['id']}").status_code == 204
    assert auth_client.get(f"{BASE}/{habit['id']}").json()["clean_days"] == 108


def test_the_home_summary_and_nothing_in_the_lists(auth_client: TestClient) -> None:
    names = ["Anki", "Beber água", "Ler", "Meditar"]
    habits = [create(auth_client, name=name) for name in names]
    mark(auth_client, habits[2]["id"], "2026-11-17")
    create(auth_client, name="Doce", kind="quit", started_on="2026-11-10")
    dashboard = auth_client.get("/api/v1/dashboard").json()
    summary = next(m for m in dashboard["modules"] if m["module"] == "habits")
    assert summary["today"] == "2026-11-17"
    assert (summary["done_today"], summary["scheduled_today"]) == (1, 4)
    assert [p["name"] for p in summary["pending"]] == ["Anki", "Beber água", "Meditar"]
    assert summary["pending_more"] == 0
    assert summary["quit"] == [
        {
            "id": summary["quit"][0]["id"],
            "name": "Doce",
            "color": "amber",
            "icon": "sparkles",
            "clean_days": 7,
        }
    ]
    assert not [a for a in dashboard["activity"] if a["module"] == "habits"]
    assert not [u for u in dashboard["upcoming"] if u["module"] == "habits"]


def test_idempotent_creation_and_sync(auth_client: TestClient) -> None:
    habit_id = "019a9c00-0000-7000-8000-0000000000aa"
    payload = {"id": habit_id, "name": "Correr", "kind": "build"}
    assert auth_client.post(BASE, json=payload).status_code == 201
    again = auth_client.post(BASE, json=payload | {"name": "Outro"})
    assert again.status_code == 200
    assert again.json()["name"] == "Correr"
    mark(auth_client, habit_id, "2026-11-17")
    since = auth_client.get(f"{BASE}/entries", params={"updated_since": "2026-11-17T00:00:00Z"})
    assert since.json()["total"] == 1
    entry_id = since.json()["items"][0]["id"]
    auth_client.delete(f"{BASE}/{habit_id}/entries/2026-11-17")
    deletions = auth_client.get(
        "/api/v1/sync/deletions", params={"since": "2026-11-01T00:00:00Z"}
    ).json()
    assert [(d["resource"], d["id"]) for d in deletions["items"]] == [("habits.entries", entry_id)]


def test_other_user_gets_404(auth_client: TestClient, other_client: TestClient) -> None:
    habit = create(auth_client)
    quit_habit = create(auth_client, name="Doce", kind="quit")
    future = auth_client.post(
        f"{BASE}/{habit['id']}/frequencies", json={"valid_from": "2026-11-23", "kind": "daily"}
    ).json()
    pause = auth_client.post(
        f"{BASE}/{habit['id']}/pauses", json={"starts_on": "2026-12-01"}
    ).json()
    relapse_habit = auth_client.post(
        f"{BASE}/{quit_habit['id']}/relapses", json={"occurred_at": "2026-11-17T10:00:00Z"}
    ).json()
    relapse_id = auth_client.get(f"{BASE}/{quit_habit['id']}").json()["relapses"][0]["id"]
    assert relapse_habit["relapses_30d"] == 1
    hid = habit["id"]
    for method, path in (
        ("get", f"{BASE}/{hid}"),
        ("delete", f"{BASE}/{hid}"),
        ("get", f"{BASE}/{hid}/calendar"),
        ("post", f"{BASE}/{hid}/archive"),
        ("delete", f"{BASE}/{hid}/entries/2026-11-17"),
        ("delete", f"{BASE}/frequencies/{future['id']}"),
        ("delete", f"{BASE}/pauses/{pause['id']}"),
        ("delete", f"{BASE}/relapses/{relapse_id}"),
    ):
        assert getattr(other_client, method)(path).status_code == 404, path
    assert other_client.put(f"{BASE}/{hid}/entries/2026-11-17", json={}).status_code == 404
    assert other_client.patch(f"{BASE}/{hid}", json={"name": "X"}).status_code == 404
    assert (
        other_client.post(f"{BASE}/{hid}/pauses", json={"starts_on": "2026-12-10"}).status_code
        == 404
    )
    assert other_client.get(BASE).json()["total"] == 0
    assert other_client.get(f"{BASE}/today").json()["items"] == []
    assert other_client.get(f"{BASE}/entries").json()["total"] == 0
