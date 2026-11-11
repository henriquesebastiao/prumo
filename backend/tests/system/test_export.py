import csv
import io
import json
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from prumo.core.config import get_settings
from tests.modules.reading.helpers import image


@pytest.fixture(autouse=True)
def uploads(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(get_settings(), "uploads_dir", tmp_path)
    return tmp_path


def archive(client: TestClient) -> zipfile.ZipFile:
    response = client.get("/api/v1/me/export")
    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == "application/zip"
    assert response.headers["content-disposition"].startswith('attachment; filename="prumo-ana-')
    return zipfile.ZipFile(io.BytesIO(response.content))


def test_export_has_json_csv_and_files(auth_client: TestClient, other_client: TestClient) -> None:
    account = auth_client.post(
        "/api/v1/finance/accounts", json={"name": "Nubank", "kind": "checking"}
    ).json()
    vehicle = auth_client.post(
        "/api/v1/garage/vehicles",
        json={
            "kind": "car",
            "name": "Strada",
            "brand": "Fiat",
            "model": "Strada",
            "year": 2021,
            "current_km": 52300,
        },
    ).json()
    book = auth_client.post(
        "/api/v1/reading/books",
        json={"title": "Código Limpo", "author": "Robert C. Martin", "total_pages": 425},
    ).json()
    auth_client.put(
        f"/api/v1/reading/books/{book['id']}/cover",
        files={"file": ("c.png", image(), "image/png")},
    )
    area = auth_client.post("/api/v1/studies/areas", json={"name": "Faculdade"}).json()
    auth_client.post("/api/v1/studies/subjects", json={"area_id": area["id"], "name": "Cálculo"})
    habit = auth_client.post("/api/v1/habits", json={"name": "Ler", "kind": "build"}).json()
    auth_client.put(f"/api/v1/habits/{habit['id']}/entries/{habit['started_on']}", json={})
    other_client.post("/api/v1/finance/accounts", json={"name": "Alheia", "kind": "cash"})

    files = archive(auth_client)
    names = set(files.namelist())
    assert {
        "data.json",
        "finance/accounts.csv",
        "finance/categories.csv",
        "finance/transactions.csv",
        "garage/vehicles.csv",
        "garage/odometer_readings.csv",
        "reading/books.csv",
        "reading/notes.csv",
        "studies/areas.csv",
        "studies/subjects.csv",
        "studies/sessions.csv",
        "habits/habits.csv",
        "habits/frequencies.csv",
        "habits/entries.csv",
        "habits/pauses.csv",
        "habits/relapses.csv",
        f"reading/covers/{book['id']}.webp",
    } <= names

    data = json.loads(files.read("data.json"))
    assert data["format"] == "prumo-export"
    assert data["user"]["username"] == "ana"
    assert "password_hash" not in json.dumps(data)
    assert data["preferences"]["enabled_modules"] == [
        "finance",
        "garage",
        "reading",
        "studies",
        "habits",
    ]
    accounts = data["modules"]["finance"]["accounts"]
    assert [a["name"] for a in accounts] == ["Nubank"]  # never another user's data
    assert accounts[0]["id"] == account["id"]
    assert "user_id" not in accounts[0]
    assert len(data["modules"]["finance"]["categories"]) == 14
    assert data["modules"]["garage"]["vehicles"][0]["id"] == vehicle["id"]
    assert data["modules"]["reading"]["books"][0]["title"] == "Código Limpo"
    assert data["modules"]["studies"]["subjects"][0]["name"] == "Cálculo"
    assert data["modules"]["habits"]["habits"][0]["name"] == "Ler"
    assert data["modules"]["habits"]["entries"][0]["day"] == habit["started_on"]

    rows = list(csv.DictReader(io.StringIO(files.read("finance/accounts.csv").decode())))
    assert rows[0]["name"] == "Nubank"
    assert rows[0]["include_in_total"] == "True"
    header = files.read("reading/progress.csv").decode().splitlines()
    assert header == ["id,book_id,page,previous_page,recorded_at,created_at,updated_at"]


def test_export_requires_a_session(client: TestClient) -> None:
    assert client.get("/api/v1/me/export").status_code == 401
