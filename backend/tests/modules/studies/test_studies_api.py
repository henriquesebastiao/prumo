"""Estudos through the API, with the clock at Tuesday 17/11/2026 14:30 in São Paulo (conftest)."""

import time_machine
from fastapi.testclient import TestClient

from tests.modules.studies.helpers import (
    BASE,
    block,
    create_area,
    create_plan,
    create_subject,
    log_session,
)


def test_areas_and_subjects(auth_client: TestClient) -> None:
    area = create_area(auth_client)
    assert area["subjects_count"] == 0
    subject = create_subject(auth_client, area["id"], obsidian_uri="obsidian://open?vault=E&file=C")
    assert subject["color"] == "blue"
    assert subject["area_name"] == "Faculdade"
    assert subject["minutes_this_week"] == 0
    assert auth_client.get(f"{BASE}/areas/{area['id']}").json()["subjects_count"] == 1

    bad = auth_client.post(
        f"{BASE}/subjects", json={"area_id": area["id"], "name": "X", "obsidian_uri": "https://x"}
    )
    assert bad.json()["error"]["code"] == "studies.invalid_obsidian_uri"
    cleared = auth_client.patch(f"{BASE}/subjects/{subject['id']}", json={"obsidian_uri": None})
    assert cleared.json()["obsidian_uri"] is None

    in_use = auth_client.delete(f"{BASE}/areas/{area['id']}")
    assert in_use.json()["error"]["code"] == "studies.area_in_use"
    archived = auth_client.post(f"{BASE}/areas/{area['id']}/archive").json()
    assert archived["archived_at"] is not None
    assert auth_client.get(f"{BASE}/areas").json()["total"] == 0
    assert auth_client.get(f"{BASE}/areas", params={"archived": "all"}).json()["total"] == 1
    assert auth_client.delete(f"{BASE}/subjects/{subject['id']}").status_code == 204
    assert auth_client.delete(f"{BASE}/areas/{area['id']}").status_code == 204


def test_sessions_create_topics_by_name_and_count_on_the_local_day(auth_client: TestClient) -> None:
    area = create_area(auth_client)
    subject = create_subject(auth_client, area["id"])
    first = log_session(
        auth_client, subject["id"], "2026-11-10T23:30:00-03:00", 60, topic_name="Integrais"
    )
    assert first["topic"]["name"] == "Integrais"
    again = log_session(
        auth_client, subject["id"], "2026-11-11T08:00:00-03:00", 20, topic_name="integrais"
    )
    assert again["topic"]["id"] == first["topic"]["id"]
    topics = auth_client.get(f"{BASE}/subjects/{subject['id']}/topics").json()["items"]
    assert [(t["name"], t["sessions_count"]) for t in topics] == [("Integrais", 2)]
    in_use = auth_client.delete(f"{BASE}/topics/{first['topic']['id']}")
    assert in_use.json()["error"]["code"] == "studies.topic_in_use"

    day = auth_client.get(f"{BASE}/day", params={"on": "2026-11-10"}).json()
    assert day["rows"][0]["done_minutes"] == 60
    assert day["rows"][0]["status"] == "extra"
    assert day["met"] is None
    sessions = auth_client.get(
        f"{BASE}/sessions", params={"from": "2026-11-11", "to": "2026-11-11"}
    )
    assert sessions.json()["total"] == 1

    detail = auth_client.get(f"{BASE}/subjects/{subject['id']}").json()
    assert len(detail["weekly_minutes"]) == 8
    assert detail["weekly_minutes"][-2]["minutes"] == 80
    assert detail["last_session_at"].startswith("2026-11-11")
    assert len(detail["recent_sessions"]) == 2

    too_long = auth_client.post(
        f"{BASE}/sessions",
        json={
            "subject_id": subject["id"],
            "started_at": "2026-11-11T08:00:00Z",
            "duration_minutes": 721,
        },
    )
    assert too_long.status_code == 422
    archived = auth_client.post(f"{BASE}/subjects/{subject['id']}/archive")
    assert archived.status_code == 200
    refused = auth_client.post(
        f"{BASE}/sessions",
        json={
            "subject_id": subject["id"],
            "started_at": "2026-11-11T08:00:00Z",
            "duration_minutes": 10,
        },
    )
    assert refused.json()["error"]["code"] == "studies.subject_archived"


def test_plan_versions_goals_statuses_and_the_week(auth_client: TestClient) -> None:
    area = create_area(auth_client)
    calc = create_subject(auth_client, area["id"])
    fastapi = create_subject(auth_client, area["id"], name="FastAPI")
    with time_machine.travel("2026-10-01T12:00:00Z"):
        old = create_plan(auth_client, "2026-10-05", [block(calc["id"], [0], 30)])
    with time_machine.travel("2026-11-01T12:00:00Z"):
        current = create_plan(
            auth_client,
            "2026-11-02",
            [block(calc["id"], [0, 2], 60, "19:00"), block(fastapi["id"], [1, 3], 45, "20:00")],
        )
    future = create_plan(auth_client, "2026-11-23", [block(calc["id"], [0], 90)])

    plans = auth_client.get(f"{BASE}/plans").json()
    assert plans["today"] == "2026-11-17"
    assert [(p["state"], p["valid_until"]) for p in plans["items"]] == [
        ("future", None),
        ("current", "2026-11-22"),
        ("past", "2026-11-01"),
    ]
    in_force = auth_client.get(f"{BASE}/plan", params={"on": "2026-10-20"}).json()
    assert in_force["plan"]["id"] == old["id"]
    assert auth_client.get(f"{BASE}/plan").json()["plan"]["id"] == current["id"]

    locked = auth_client.put(f"{BASE}/plans/{old['id']}", json={"blocks": []})
    assert locked.json()["error"]["code"] == "studies.plan_locked"
    assert auth_client.delete(f"{BASE}/plans/{current['id']}").status_code == 422
    taken = auth_client.post(f"{BASE}/plans", json={"valid_from": "2026-11-23", "blocks": []})
    assert taken.status_code == 409
    assert taken.json()["error"]["code"] == "studies.plan_date_taken"
    past = auth_client.post(f"{BASE}/plans", json={"valid_from": "2026-11-16", "blocks": []})
    assert past.json()["error"]["code"] == "studies.plan_locked"
    edited = auth_client.put(
        f"{BASE}/plans/{future['id']}", json={"blocks": [block(fastapi["id"], [5], 120)]}
    ).json()
    assert [b["subject"]["name"] for b in edited["blocks"]] == ["FastAPI"]
    assert auth_client.delete(f"{BASE}/plans/{future['id']}").status_code == 204

    # Monday 16/11: Cálculo met, Tuesday 17 (today): FastAPI partial, in progress for the rest.
    log_session(auth_client, calc["id"], "2026-11-16T19:00:00-03:00", 60)
    log_session(auth_client, fastapi["id"], "2026-11-17T13:00:00-03:00", 15)
    monday = auth_client.get(f"{BASE}/day", params={"on": "2026-11-16"}).json()
    assert [(r["subject"]["name"], r["status"]) for r in monday["rows"]] == [("Cálculo II", "met")]
    assert monday["met"] is True
    today = auth_client.get(f"{BASE}/day").json()
    assert today["is_today"] is True
    assert [(r["status"], r["goal_minutes"], r["done_minutes"]) for r in today["rows"]] == [
        ("partial", 45, 15)
    ]
    assert today["rows"][0]["blocks"][0]["starts_at"] == "20:00:00"
    week = auth_client.get(f"{BASE}/week").json()
    assert (week["start"], week["end"]) == ("2026-11-16", "2026-11-22")
    assert (week["days_met"], week["days_planned"]) == (1, 2)
    assert (week["minutes_done"], week["minutes_planned"]) == (75, 210)
    assert week["days"][2]["rows"][0]["status"] == "in_progress"
    assert week["next_start"] == "2026-11-23"
    assert (
        auth_client.get(f"{BASE}/week", params={"start": "2026-11-25"}).json()["next_start"] is None
    )
    last_week = auth_client.get(f"{BASE}/week", params={"start": "2026-11-11"}).json()
    assert last_week["days"][0]["rows"][0]["status"] == "missed"
    assert last_week["days_planned"] == 4
    assert [s["subject"]["name"] for s in week["by_subject"]] == ["Cálculo II", "FastAPI"]

    overview = auth_client.get(f"{BASE}/overview").json()
    assert (overview["subjects_count"], overview["sessions_this_month"]) == (2, 2)


def test_the_home_shows_today_and_the_sessions(auth_client: TestClient) -> None:
    area = create_area(auth_client, name="Inglês", color="orange")
    english = create_subject(auth_client, area["id"], name="Inglês")
    create_plan(auth_client, "2026-11-17", [block(english["id"], [1], 30, "07:00")])
    log_session(auth_client, english["id"], "2026-11-17T07:05:00-03:00", 30, topic_name="Listening")
    dashboard = auth_client.get("/api/v1/dashboard").json()
    summary = next(m for m in dashboard["modules"] if m["module"] == "studies")
    assert summary["today"] == "2026-11-17"
    assert summary["done_minutes_today"] == 30
    assert summary["blocks_today"][0]["status"] == "met"
    assert summary["week"]["days_met"] == 1
    activity = [a for a in dashboard["activity"] if a["module"] == "studies"]
    assert activity[0]["kind"] == "studies.session"
    assert activity[0]["subject"] == "Inglês"
    assert activity[0]["entity_id"] == english["id"]
    assert activity[0]["data"]["topic"] == "Listening"
    assert activity[0]["data"]["color"] == "orange"
    assert not [u for u in dashboard["upcoming"] if u["module"] == "studies"]


def test_idempotent_creation_and_sync(auth_client: TestClient) -> None:
    area = create_area(auth_client)
    subject = create_subject(auth_client, area["id"])
    session_id = "019a9c00-0000-7000-8000-000000000001"
    payload = {
        "id": session_id,
        "subject_id": subject["id"],
        "started_at": "2026-11-17T10:00:00Z",
        "duration_minutes": 25,
    }
    first = auth_client.post(f"{BASE}/sessions", json=payload)
    assert first.status_code == 201
    second = auth_client.post(f"{BASE}/sessions", json=payload | {"duration_minutes": 50})
    assert second.status_code == 200
    assert second.json()["duration_minutes"] == 25
    since = auth_client.get(f"{BASE}/sessions", params={"updated_since": "2026-11-17T00:00:00Z"})
    assert since.json()["total"] == 1
    auth_client.delete(f"{BASE}/sessions/{session_id}")
    # The deletion is stamped by the database clock (real time), not the frozen test clock.
    deletions = auth_client.get(
        "/api/v1/sync/deletions", params={"since": "2026-11-01T00:00:00Z"}
    ).json()
    assert [(d["resource"], d["id"]) for d in deletions["items"]] == [
        ("studies.sessions", session_id)
    ]


def test_other_user_gets_404(auth_client: TestClient, other_client: TestClient) -> None:
    area = create_area(auth_client)
    subject = create_subject(auth_client, area["id"])
    plan = create_plan(auth_client, "2026-11-23", [block(subject["id"], [0])])
    item = log_session(auth_client, subject["id"], "2026-11-17T10:00:00Z")
    for path in (
        f"{BASE}/areas/{area['id']}",
        f"{BASE}/subjects/{subject['id']}",
        f"{BASE}/plans/{plan['id']}",
        f"{BASE}/sessions/{item['id']}",
    ):
        assert other_client.get(path).status_code == 404, path
        assert other_client.delete(path).status_code == 404, path
    assert (
        other_client.post(f"{BASE}/subjects", json={"area_id": area["id"], "name": "X"}).status_code
        == 404
    )
    assert (
        other_client.post(
            f"{BASE}/sessions",
            json={
                "subject_id": subject["id"],
                "started_at": "2026-11-17T10:00:00Z",
                "duration_minutes": 5,
            },
        ).status_code
        == 404
    )
    assert other_client.get(f"{BASE}/plan").json()["plan"] is None
    assert other_client.get(f"{BASE}/day").json()["rows"] == []
