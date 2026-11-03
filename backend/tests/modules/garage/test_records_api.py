import time_machine
from fastapi.testclient import TestClient

from tests.modules.garage.helpers import BASE, add_fueling, add_maintenance, create_vehicle

# ---------------------------------------------------------------- odometer (G2, G3)


def test_odometer_consistency(auth_client: TestClient) -> None:
    vehicle = create_vehicle(auth_client)  # 18420 km now
    url = f"{BASE}/vehicles/{vehicle['id']}/odometer"
    assert auth_client.post(url, json={"km": 18420}).status_code == 201  # equal is fine
    lower = auth_client.post(url, json={"km": 18300})
    assert lower.status_code == 422
    error = lower.json()["error"]
    assert error["code"] == "garage.odometer_inconsistent"
    assert error["details"]["conflict"] == "previous"
    assert error["details"]["km"] == 18420
    past = auth_client.post(url, json={"km": 18500, "recorded_at": "2026-11-01T12:00:00Z"})
    assert past.status_code == 422
    assert past.json()["error"]["details"]["conflict"] == "next"
    backfill = auth_client.post(url, json={"km": 17000, "recorded_at": "2026-10-01T12:00:00Z"})
    assert backfill.status_code == 201
    assert auth_client.get(f"{BASE}/vehicles/{vehicle['id']}").json()["current_km"] == 18420


def test_deleting_readings(auth_client: TestClient) -> None:
    vehicle = create_vehicle(auth_client)
    url = f"{BASE}/vehicles/{vehicle['id']}/odometer"
    first = auth_client.get(url).json()["items"][0]
    last_one = auth_client.delete(f"{url}/{first['id']}")
    assert last_one.status_code == 422
    assert last_one.json()["error"]["code"] == "garage.last_reading"

    newer = auth_client.post(url, json={"km": 18600}).json()
    assert auth_client.get(f"{BASE}/vehicles/{vehicle['id']}").json()["current_km"] == 18600
    assert auth_client.delete(f"{url}/{newer['id']}").status_code == 204
    assert auth_client.get(f"{BASE}/vehicles/{vehicle['id']}").json()["current_km"] == 18420

    fueling = add_fueling(auth_client, vehicle["id"], km=18700, fueled_at="2026-11-17T18:00:00Z")
    from_fueling = next(r for r in auth_client.get(url).json()["items"] if r["source"] == "fueling")
    assert from_fueling["source_id"] == fueling["id"]
    not_manual = auth_client.delete(f"{url}/{from_fueling['id']}")
    assert not_manual.status_code == 422
    assert not_manual.json()["error"]["code"] == "garage.reading_not_manual"


# ---------------------------------------------------------------- maintenances (G4, G5, G10)


def test_maintenance_totals_items_and_workshop_by_name(auth_client: TestClient) -> None:
    vehicle = create_vehicle(auth_client)
    maintenance = add_maintenance(auth_client, vehicle["id"])
    assert maintenance["parts_cents"] == 18990 + 2 * 1725
    assert maintenance["total_cents"] == 18990 + 2 * 1725 + 6000
    assert [item["quantity"] for item in maintenance["items"]] == [1, 2]
    assert maintenance["workshop"]["name"] == "Moto Peças Rocha"
    assert maintenance["vehicle"]["name"] == "Honda CG 160 Fan"
    # The same name, in another case, reuses the workshop.
    second = add_maintenance(
        auth_client,
        vehicle["id"],
        workshop_name="moto peças rocha",
        km=16500,
        performed_at="2026-10-01T12:00:00Z",
    )
    assert second["workshop"]["id"] == maintenance["workshop"]["id"]
    workshops = auth_client.get(f"{BASE}/workshops?q=rocha").json()
    assert workshops["total"] == 1
    assert workshops["items"][0]["maintenances_count"] == 2
    assert workshops["items"][0]["last_maintenance_at"] == "2026-10-01T12:00:00Z"


def test_update_maintenance_replaces_items_and_moves_the_reading(auth_client: TestClient) -> None:
    vehicle = create_vehicle(auth_client)
    maintenance = add_maintenance(auth_client, vehicle["id"])
    url = f"{BASE}/vehicles/{vehicle['id']}/maintenances/{maintenance['id']}"
    response = auth_client.patch(
        url,
        json={
            "km": 16200,
            "labor_cost_cents": 0,
            "items": [{"description": "Lona de freio", "unit_price_cents": 3890}],
            "workshop_name": None,
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total_cents"] == 3890
    assert [item["description"] for item in body["items"]] == ["Lona de freio"]
    assert body["workshop"] is None
    readings = auth_client.get(f"{BASE}/vehicles/{vehicle['id']}/odometer").json()["items"]
    assert any(r["source"] == "maintenance" and r["km"] == 16200 for r in readings)
    assert auth_client.patch(url, json={"km": 99999}).status_code == 422
    assert auth_client.delete(url).status_code == 204
    readings = auth_client.get(f"{BASE}/vehicles/{vehicle['id']}/odometer").json()["items"]
    assert all(r["source"] != "maintenance" for r in readings)


def test_oil_change_suggestion_and_defaults(auth_client: TestClient) -> None:
    vehicle = create_vehicle(auth_client)
    vid = vehicle["id"]
    suggestion = auth_client.get(
        f"{BASE}/vehicles/{vid}/oil-change-suggestion?km=18420&on=2026-11-17"
    ).json()
    assert suggestion["next_oil_change_km"] == 19420
    assert suggestion["next_oil_change_on"] == "2027-02-17"
    assert suggestion["previous_oil_types"] == []

    suggested = auth_client.post(
        f"{BASE}/vehicles/{vid}/maintenances",
        json={
            "kind": "oil_change",
            "performed_at": "2026-11-17T12:00:00Z",
            "km": 18420,
            "oil_type": "4T 20W-50 semissintético",
        },
    ).json()
    assert (suggested["next_oil_change_km"], suggested["next_oil_change_on"]) == (
        19420,
        "2027-02-17",
    )

    custom = auth_client.post(
        f"{BASE}/vehicles/{vid}/maintenances",
        json={
            "kind": "oil_change",
            "performed_at": "2026-11-17T13:00:00Z",
            "km": 18420,
            "oil_type": "4T 10W-30 sintético",
            "next_oil_change_km": 19000,
            "next_oil_change_on": None,
        },
    ).json()
    assert (custom["next_oil_change_km"], custom["next_oil_change_on"]) == (19000, None)

    later = auth_client.get(f"{BASE}/vehicles/{vid}/oil-change-suggestion").json()
    assert later["previous_oil_types"] == ["4T 10W-30 sintético", "4T 20W-50 semissintético"]
    oil = auth_client.get(f"{BASE}/vehicles/{vid}").json()["oil_change"]
    assert oil["next_km"] == 19000  # the most recent oil change wins
    assert oil["next_on"] is None
    assert oil["primary"] == "km"


def test_oil_fields_require_an_oil_change(auth_client: TestClient) -> None:
    vehicle = create_vehicle(auth_client)
    response = auth_client.post(
        f"{BASE}/vehicles/{vehicle['id']}/maintenances",
        json={"performed_at": "2026-11-17T12:00:00Z", "km": 18420, "oil_type": "5W30"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["fields"][0]["code"] == "garage.oil_fields_require_oil_change"
    general = add_maintenance(auth_client, vehicle["id"])
    patch = auth_client.patch(
        f"{BASE}/vehicles/{vehicle['id']}/maintenances/{general['id']}", json={"oil_type": "5W30"}
    )
    assert patch.status_code == 422
    assert patch.json()["error"]["code"] == "garage.oil_fields_require_oil_change"


def test_cross_vehicle_maintenance_list_filters(auth_client: TestClient) -> None:
    cg = create_vehicle(auth_client)
    strada = create_vehicle(auth_client, name="Strada", kind="car", current_km=52300)
    first = add_maintenance(auth_client, cg["id"])
    add_maintenance(auth_client, strada["id"], km=50000, workshop_name="Auto Center")
    auth_client.post(
        f"{BASE}/vehicles/{cg['id']}/maintenances",
        json={"kind": "oil_change", "performed_at": "2026-11-17T12:00:00Z", "km": 18420},
    )
    everything = auth_client.get(f"{BASE}/maintenances").json()
    assert everything["total"] == 3
    assert everything["items"][0]["kind"] == "oil_change"  # newest first
    only_cg = auth_client.get(f"{BASE}/maintenances?vehicle_id={cg['id']}").json()
    assert only_cg["total"] == 2
    oil_only = auth_client.get(f"{BASE}/maintenances?kind=oil_change").json()
    assert oil_only["total"] == 1
    workshop = first["workshop"]["id"]
    assert auth_client.get(f"{BASE}/maintenances?workshop_id={workshop}").json()["total"] == 1
    nested = auth_client.get(f"{BASE}/vehicles/{cg['id']}/maintenances?kind=general").json()
    assert nested["total"] == 1


# ---------------------------------------------------------------- fuelings (G7, G8)


def test_fueling_defaults_price_and_consumption(auth_client: TestClient) -> None:
    vehicle = create_vehicle(auth_client)
    vid = vehicle["id"]
    first = add_fueling(auth_client, vid, fueled_at="2026-11-17T18:00:00Z", km=18500)
    assert first["fuel_type"] == "gasoline"  # the vehicle's usual fuel
    assert first["price_per_liter"] == 6.351
    assert first["consumption_km_l"] is None  # first full tank
    second = add_fueling(
        auth_client,
        vid,
        fueled_at="2026-11-17T19:00:00Z",
        km=18800,
        volume_ml=7500,
        fuel_type="ethanol",
    )
    assert second["consumption_km_l"] == 40.0
    assert second["fuel_type"] == "ethanol"
    listed = auth_client.get(f"{BASE}/vehicles/{vid}/fuelings").json()["items"]
    assert [f["consumption_km_l"] for f in listed] == [40.0, None]

    no_fuel = create_vehicle(auth_client, name="Sem combustível", fuel_type=None)
    response = auth_client.post(
        f"{BASE}/vehicles/{no_fuel['id']}/fuelings",
        json={
            "fueled_at": "2026-11-17T18:00:00Z",
            "km": 18500,
            "volume_ml": 1000,
            "total_cents": 600,
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "garage.fuel_type_required"


def test_update_and_delete_fueling(auth_client: TestClient) -> None:
    vehicle = create_vehicle(auth_client)
    fueling = add_fueling(auth_client, vehicle["id"], fueled_at="2026-11-17T18:00:00Z", km=18500)
    url = f"{BASE}/vehicles/{vehicle['id']}/fuelings/{fueling['id']}"
    updated = auth_client.patch(url, json={"km": 18510, "full_tank": False}).json()
    assert (updated["km"], updated["full_tank"]) == (18510, False)
    assert auth_client.get(f"{BASE}/vehicles/{vehicle['id']}").json()["current_km"] == 18510
    assert auth_client.patch(url, json={"km": 1}).status_code == 422
    assert auth_client.patch(url, json={"volume_ml": 0}).status_code == 422
    assert auth_client.delete(url).status_code == 204
    assert auth_client.get(f"{BASE}/vehicles/{vehicle['id']}").json()["current_km"] == 18420


def test_cross_vehicle_fueling_list_with_days(auth_client: TestClient) -> None:
    cg = create_vehicle(auth_client)
    strada = create_vehicle(auth_client, name="Strada", kind="car", current_km=52400)
    add_fueling(auth_client, cg["id"])  # 16/11 18:10 in São Paulo
    add_fueling(
        auth_client, strada["id"], km=52300, fueled_at="2026-11-14T02:30:00Z"
    )  # 13/11 23:30
    assert auth_client.get(f"{BASE}/fuelings").json()["total"] == 2
    november_14 = auth_client.get(f"{BASE}/fuelings?from=2026-11-14&to=2026-11-14").json()
    assert november_14["total"] == 0  # the 02:30 UTC fueling is still the 13th in São Paulo
    from_13 = auth_client.get(f"{BASE}/fuelings?from=2026-11-13&to=2026-11-13").json()
    assert [f["vehicle"]["name"] for f in from_13["items"]] == ["Strada"]


# ---------------------------------------------------------------- workshops


def test_workshop_crud(auth_client: TestClient) -> None:
    created = auth_client.post(f"{BASE}/workshops", json={"name": "Auto Center"})
    assert created.status_code == 201
    workshop = created.json()
    assert workshop["maintenances_count"] == 0
    duplicate = auth_client.post(f"{BASE}/workshops", json={"name": "auto center"})
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "garage.workshop_exists"
    renamed = auth_client.patch(f"{BASE}/workshops/{workshop['id']}", json={"name": "Centro"})
    assert renamed.json()["name"] == "Centro"
    vehicle = create_vehicle(auth_client)
    add_maintenance(auth_client, vehicle["id"], workshop_name=None, workshop_id=workshop["id"])
    in_use = auth_client.delete(f"{BASE}/workshops/{workshop['id']}")
    assert in_use.status_code == 422
    assert in_use.json()["error"]["code"] == "garage.workshop_in_use"
    free = auth_client.post(f"{BASE}/workshops", json={"name": "Livre"}).json()
    assert auth_client.delete(f"{BASE}/workshops/{free['id']}").status_code == 204


# ---------------------------------------------------------------- overview and Início


def _design_fleet(client: TestClient) -> tuple[dict[str, object], dict[str, object]]:
    with time_machine.travel("2026-10-01T12:00:00Z"):
        cg = create_vehicle(client, current_km=17000)
        strada = create_vehicle(
            client,
            name="Fiat Strada Freedom",
            kind="car",
            current_km=46000,
            oil_interval_km=10000,
            oil_interval_months=12,
        )
    client.post(
        f"{BASE}/vehicles/{cg['id']}/maintenances",
        json={"kind": "oil_change", "performed_at": "2026-10-21T13:00:00Z", "km": 17640},
    )
    client.post(
        f"{BASE}/vehicles/{strada['id']}/maintenances",
        json={
            "kind": "oil_change",
            "performed_at": "2026-10-02T13:00:00Z",
            "km": 46900,
            "next_oil_change_km": 56900,
            "next_oil_change_on": "2026-12-05",
        },
    )
    add_fueling(client, cg["id"], fueled_at="2026-10-30T12:00:00Z", km=17957, volume_ml=8000)
    add_fueling(client, cg["id"])
    add_fueling(
        client,
        strada["id"],
        km=52300,
        fueled_at="2026-11-13T22:00:00Z",
        volume_ml=28400,
        total_cents=18034,
    )
    client.post(f"{BASE}/vehicles/{cg['id']}/odometer", json={"km": 18420})
    return cg, strada


def test_overview(auth_client: TestClient) -> None:
    _design_fleet(auth_client)
    overview = auth_client.get(f"{BASE}/overview").json()
    assert overview["month"] == "2026-11"
    assert overview["month_fuel_cents"] == 4636 + 18034
    assert overview["month_fuelings_count"] == 2
    assert {item["vehicle"]["name"]: item["km"] for item in overview["vehicles_km"]} == {
        "Honda CG 160 Fan": 463,
        "Fiat Strada Freedom": 5400,
    }
    # Like the design: "Próximo vencimento 220 km · Óleo da CG 160 · ≈ 25/11" (by pace).
    next_due = overview["next_due"]
    assert next_due["vehicle"]["name"] == "Honda CG 160 Fan"
    assert next_due["primary"] == "km"
    assert next_due["remaining_km"] == 220
    assert next_due["due_on"] == "2026-11-25"


def test_dashboard_summary_upcoming_and_activity(auth_client: TestClient) -> None:
    _design_fleet(auth_client)
    body = auth_client.get("/api/v1/dashboard").json()
    summary = next(m for m in body["modules"] if m["module"] == "garage")
    assert summary["vehicles_count"] == 2
    assert [v["vehicle"]["name"] for v in summary["vehicles"]] == [
        "Honda CG 160 Fan",
        "Fiat Strada Freedom",
    ]
    assert summary["vehicles"][0]["oil_primary"] == "km"
    assert summary["vehicles"][0]["remaining_km"] == 220
    assert summary["vehicles"][1]["oil_primary"] == "date"
    assert summary["vehicles"][1]["remaining_days"] == 18

    upcoming = [item for item in body["upcoming"] if item["module"] == "garage"]
    assert [(item["subject"], item["data"]["basis"]) for item in upcoming][-1] == (
        "Fiat Strada Freedom",
        "date",
    )
    assert all(item["kind"] == "garage.oil_change" for item in upcoming)

    activity = body["activity"]
    assert activity[0]["kind"] == "garage.odometer"
    assert activity[0]["data"] == {"km": 18420}
    kinds = {item["kind"] for item in activity}
    assert {"garage.fueling", "garage.maintenance"} <= kinds
