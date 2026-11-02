"""Helpers that create garage records through the API, like a client would."""

from typing import Any

from fastapi.testclient import TestClient

BASE = "/api/v1/garage"


def vehicle_payload(**overrides: Any) -> dict[str, Any]:
    return {
        "kind": "motorcycle",
        "name": "Honda CG 160 Fan",
        "brand": "Honda",
        "model": "CG 160 Fan",
        "year": 2023,
        "fuel_type": "gasoline",
        "current_km": 18420,
        "oil_interval_km": 1000,
        "oil_interval_months": 3,
    } | overrides


def create_vehicle(client: TestClient, **overrides: Any) -> dict[str, Any]:
    response = client.post(f"{BASE}/vehicles", json=vehicle_payload(**overrides))
    assert response.status_code == 201, response.text
    body: dict[str, Any] = response.json()
    return body


def add_fueling(client: TestClient, vehicle_id: str, **overrides: Any) -> dict[str, Any]:
    payload = {
        "fueled_at": "2026-11-16T21:10:00Z",
        "km": 18400,
        "volume_ml": 7300,
        "total_cents": 4636,
        "full_tank": True,
    } | overrides
    response = client.post(f"{BASE}/vehicles/{vehicle_id}/fuelings", json=payload)
    assert response.status_code == 201, response.text
    body: dict[str, Any] = response.json()
    return body


def add_maintenance(client: TestClient, vehicle_id: str, **overrides: Any) -> dict[str, Any]:
    payload = {
        "performed_at": "2026-09-03T13:30:00Z",
        "km": 16180,
        "workshop_name": "Moto Peças Rocha",
        "labor_cost_cents": 6000,
        "items": [
            {"description": "Kit relação", "unit_price_cents": 18990},
            {"description": "Pastilha de freio", "quantity": 2, "unit_price_cents": 1725},
        ],
    } | overrides
    response = client.post(f"{BASE}/vehicles/{vehicle_id}/maintenances", json=payload)
    assert response.status_code == 201, response.text
    body: dict[str, Any] = response.json()
    return body
