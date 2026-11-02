import time_machine
from fastapi.testclient import TestClient

from tests.modules.garage.conftest import NOW
from tests.modules.garage.helpers import BASE, add_fueling, add_maintenance, create_vehicle


def test_create_vehicle_records_the_first_reading(auth_client: TestClient) -> None:
    vehicle = create_vehicle(auth_client)
    assert vehicle["current_km"] == 18420
    assert vehicle["oil_change"]["status"] == "unknown"
    assert vehicle["stats"]["last_fueling"] is None
    readings = auth_client.get(f"{BASE}/vehicles/{vehicle['id']}/odometer").json()
    assert readings["total"] == 1
    assert readings["items"][0]["source"] == "manual"


def test_vehicle_without_intervals_has_no_oil_status(auth_client: TestClient) -> None:
    vehicle = create_vehicle(auth_client, oil_interval_km=None, oil_interval_months=None)
    assert vehicle["oil_change"] is None


def test_vehicle_validation(auth_client: TestClient) -> None:
    response = auth_client.post(
        f"{BASE}/vehicles",
        json={
            "kind": "boat",
            "name": "",
            "brand": "X",
            "model": "Y",
            "year": 1800,
            "current_km": -1,
        },
    )
    assert response.status_code == 422
    paths = {field["path"] for field in response.json()["error"]["fields"]}
    assert {"kind", "name", "year", "current_km"} <= paths


def test_update_vehicle_and_km_from_the_edit_form(auth_client: TestClient) -> None:
    vehicle = create_vehicle(auth_client)
    response = auth_client.patch(
        f"{BASE}/vehicles/{vehicle['id']}",
        json={"name": "CG", "current_km": 18512, "oil_interval_months": None},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "CG"
    assert body["current_km"] == 18512
    assert body["oil_interval_months"] is None
    assert auth_client.get(f"{BASE}/vehicles/{vehicle['id']}/odometer").json()["total"] == 2
    null_name = auth_client.patch(f"{BASE}/vehicles/{vehicle['id']}", json={"name": None})
    assert null_name.status_code == 422
    lower = auth_client.patch(f"{BASE}/vehicles/{vehicle['id']}", json={"current_km": 100})
    assert lower.status_code == 422
    assert lower.json()["error"]["code"] == "garage.odometer_inconsistent"


def test_archive_filter_and_delete(auth_client: TestClient) -> None:
    kept = create_vehicle(auth_client, name="Strada")
    archived = create_vehicle(auth_client, name="Antiga")
    auth_client.post(f"{BASE}/vehicles/{archived['id']}/archive")
    names = [v["name"] for v in auth_client.get(f"{BASE}/vehicles").json()["items"]]
    assert names == ["Strada"]
    archived_only = auth_client.get(f"{BASE}/vehicles?archived=true").json()["items"]
    assert [v["name"] for v in archived_only] == ["Antiga"]
    assert archived_only[0]["archived_at"] is not None
    assert auth_client.get(f"{BASE}/vehicles?archived=all").json()["total"] == 2
    unarchived = auth_client.post(f"{BASE}/vehicles/{archived['id']}/unarchive").json()
    assert unarchived["archived_at"] is None
    assert auth_client.delete(f"{BASE}/vehicles/{kept['id']}").status_code == 204
    assert auth_client.get(f"{BASE}/vehicles/{kept['id']}").status_code == 404


def test_other_user_gets_404_everywhere(auth_client: TestClient, other_client: TestClient) -> None:
    vehicle = create_vehicle(auth_client)
    fueling = add_fueling(auth_client, vehicle["id"])
    maintenance = add_maintenance(auth_client, vehicle["id"])
    reading = auth_client.get(f"{BASE}/vehicles/{vehicle['id']}/odometer").json()["items"][0]
    workshop = auth_client.get(f"{BASE}/workshops").json()["items"][0]
    vid = vehicle["id"]
    requests = [
        ("GET", f"{BASE}/vehicles/{vid}"),
        ("PATCH", f"{BASE}/vehicles/{vid}"),
        ("DELETE", f"{BASE}/vehicles/{vid}"),
        ("POST", f"{BASE}/vehicles/{vid}/archive"),
        ("GET", f"{BASE}/vehicles/{vid}/odometer"),
        ("DELETE", f"{BASE}/vehicles/{vid}/odometer/{reading['id']}"),
        ("GET", f"{BASE}/vehicles/{vid}/maintenances/{maintenance['id']}"),
        ("PATCH", f"{BASE}/vehicles/{vid}/maintenances/{maintenance['id']}"),
        ("DELETE", f"{BASE}/vehicles/{vid}/maintenances/{maintenance['id']}"),
        ("GET", f"{BASE}/vehicles/{vid}/fuelings/{fueling['id']}"),
        ("PATCH", f"{BASE}/vehicles/{vid}/fuelings/{fueling['id']}"),
        ("DELETE", f"{BASE}/vehicles/{vid}/fuelings/{fueling['id']}"),
        ("GET", f"{BASE}/vehicles/{vid}/oil-change-suggestion"),
        ("PATCH", f"{BASE}/workshops/{workshop['id']}"),
        ("DELETE", f"{BASE}/workshops/{workshop['id']}"),
    ]
    for method, url in requests:
        body: dict[str, object] | None = {} if method == "PATCH" else None
        response = other_client.request(method, url, json=body)
        assert response.status_code == 404, (method, url, response.text)
        assert response.json()["error"]["code"] == "not_found"
    # Lists only show the caller's records.
    for url in ("/vehicles", "/maintenances", "/fuelings", "/workshops"):
        assert other_client.get(f"{BASE}{url}").json()["total"] == 0, url
    # Referencing another user's workshop in a body is also a 404.
    own = create_vehicle(other_client)
    response = other_client.post(
        f"{BASE}/vehicles/{own['id']}/maintenances",
        json={"performed_at": NOW, "km": 18500, "workshop_id": workshop["id"]},
    )
    assert response.status_code == 404


def test_vehicle_quick_info(auth_client: TestClient) -> None:
    with time_machine.travel("2026-10-01T12:00:00Z"):
        vehicle = create_vehicle(auth_client, current_km=17000)
    vid = vehicle["id"]
    auth_client.post(
        f"{BASE}/vehicles/{vid}/maintenances",
        json={
            "kind": "oil_change",
            "performed_at": "2026-10-21T13:00:00Z",
            "km": 17640,
            "oil_type": "4T 20W-50 semissintético",
        },
    )
    add_fueling(auth_client, vid, fueled_at="2026-10-30T12:00:00Z", km=17957, volume_ml=8000)
    add_fueling(
        auth_client,
        vid,
        fueled_at="2026-11-10T12:00:00Z",
        km=18100,
        volume_ml=3000,
        full_tank=False,
    )
    add_fueling(auth_client, vid, fueled_at="2026-11-16T21:10:00Z", km=18400, volume_ml=7300)
    auth_client.post(f"{BASE}/vehicles/{vid}/odometer", json={"km": 18420})

    body = auth_client.get(f"{BASE}/vehicles/{vid}").json()
    oil = body["oil_change"]
    assert oil["status"] == "ok"
    assert oil["primary"] == "km"
    assert (oil["next_km"], oil["remaining_km"], oil["used_km_percent"]) == (18640, 220, 78)
    assert (oil["next_on"], oil["remaining_days"]) == ("2027-01-21", 65)
    assert oil["last"]["oil_type"] == "4T 20W-50 semissintético"
    assert oil["estimated_km_on"] is not None

    stats = body["stats"]
    assert stats["last_fueling"]["price_per_liter"] == 6.351
    # (18400 - 17957) km / (3.0 + 7.3) L
    assert stats["last_consumption_km_l"] == 43.01
    assert [point["km_l"] for point in stats["recent_consumption"]] == [43.01]
    assert stats["month_km"] == 463
    assert stats["month_fuelings_count"] == 2
    assert stats["month_maintenances_count"] == 0
    assert stats["month_spent_cents"] == 4636 * 2
    assert stats["pace_km_per_day"] is not None
