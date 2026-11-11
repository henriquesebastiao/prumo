"""Helpers that create studies records through the API, like a client would."""

from typing import Any

from fastapi.testclient import TestClient

BASE = "/api/v1/studies"


def create_area(client: TestClient, **overrides: Any) -> dict[str, Any]:
    response = client.post(f"{BASE}/areas", json={"name": "Faculdade", "color": "blue"} | overrides)
    assert response.status_code == 201, response.text
    body: dict[str, Any] = response.json()
    return body


def create_subject(client: TestClient, area_id: str, **overrides: Any) -> dict[str, Any]:
    payload = {"area_id": area_id, "name": "Cálculo II"} | overrides
    response = client.post(f"{BASE}/subjects", json=payload)
    assert response.status_code == 201, response.text
    body: dict[str, Any] = response.json()
    return body


def create_plan(
    client: TestClient, valid_from: str, blocks: list[dict[str, Any]]
) -> dict[str, Any]:
    response = client.post(f"{BASE}/plans", json={"valid_from": valid_from, "blocks": blocks})
    assert response.status_code == 201, response.text
    body: dict[str, Any] = response.json()
    return body


def block(
    subject_id: str, weekdays: list[int], minutes: int = 60, starts_at: str | None = None
) -> dict[str, Any]:
    return {
        "subject_id": subject_id,
        "weekdays": weekdays,
        "starts_at": starts_at,
        "duration_minutes": minutes,
    }


def log_session(
    client: TestClient, subject_id: str, started_at: str, minutes: int = 30, **overrides: Any
) -> dict[str, Any]:
    payload = {"subject_id": subject_id, "started_at": started_at, "duration_minutes": minutes}
    response = client.post(f"{BASE}/sessions", json=payload | overrides)
    assert response.status_code == 201, response.text
    body: dict[str, Any] = response.json()
    return body
