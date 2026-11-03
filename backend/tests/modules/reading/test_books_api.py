import time_machine
from fastapi.testclient import TestClient

from tests.modules.reading.helpers import BASE, create_book, progress


def test_create_defaults_and_validation(auth_client: TestClient) -> None:
    book = create_book(auth_client)
    assert book["status"] == "want_to_read"
    assert book["owned"] is False
    assert book["current_page"] == 0
    assert book["progress_percent"] == 0
    assert book["remaining_pages"] == 425
    assert book["pace_pages_per_day"] is None
    assert book["has_cover"] is False
    assert book["notes_count"] == 0

    response = auth_client.post(
        f"{BASE}/books", json={"title": "", "author": "X", "total_pages": 0, "status": "lost"}
    )
    assert response.status_code == 422
    paths = {field["path"] for field in response.json()["error"]["fields"]}
    assert {"title", "total_pages", "status"} <= paths


def test_create_a_book_already_begun_or_read(auth_client: TestClient) -> None:
    begun = create_book(auth_client, current_page=120)
    assert begun["status"] == "reading"
    assert begun["started_on"] == "2026-11-17"
    assert begun["pace_pages_per_day"] is None  # the starting point is not progress
    history = auth_client.get(f"{BASE}/books/{begun['id']}/progress").json()["items"]
    assert [(item["page"], item["pages"]) for item in history] == [(120, 0)]

    read = create_book(auth_client, title="Dom Casmurro", total_pages=256, status="read")
    assert (read["current_page"], read["progress_percent"]) == (256, 100)
    assert read["finished_on"] == "2026-11-17"
    assert read["started_on"] is None

    dated = create_book(
        auth_client, status="reading", started_on="2026-10-26", current_page=0, owned=True
    )
    assert dated["started_on"] == "2026-10-26"
    assert dated["owned"] is True

    too_far = auth_client.post(
        f"{BASE}/books", json={"title": "X", "author": "Y", "total_pages": 10, "current_page": 11}
    )
    assert too_far.json()["error"]["code"] == "reading.page_out_of_range"
    backwards = auth_client.post(
        f"{BASE}/books",
        json={
            "title": "X",
            "author": "Y",
            "total_pages": 10,
            "status": "read",
            "started_on": "2026-11-10",
            "finished_on": "2026-11-01",
        },
    )
    assert backwards.json()["error"]["code"] == "reading.invalid_dates"


def test_progress_moves_status_and_dates(auth_client: TestClient) -> None:
    book = create_book(auth_client)
    with time_machine.travel("2026-11-10T12:00:00Z"):
        reading = progress(auth_client, book["id"], 98)
    assert reading["status"] == "reading"
    assert reading["started_on"] == "2026-11-10"
    assert reading["pace_pages_per_day"] == 98.0
    assert reading["forecast_finish_on"] == "2026-11-14"
    later = progress(auth_client, book["id"], 212)
    assert later["progress_percent"] == 50
    assert later["last_progress_at"].startswith("2026-11-17")
    assert later["pace_pages_per_day"] == 29.3
    same = progress(auth_client, book["id"], 212)  # same page: no new record
    assert same["current_page"] == 212
    finished = progress(auth_client, book["id"], 425)
    assert finished["status"] == "read"
    assert finished["finished_on"] == "2026-11-17"
    assert finished["forecast_finish_on"] is None
    assert finished["pace_pages_per_day"] is None

    history = auth_client.get(f"{BASE}/books/{book['id']}/progress").json()["items"]
    assert [(item["page"], item["pages"]) for item in history] == [
        (425, 213),
        (212, 114),
        (98, 98),
    ]
    out = auth_client.post(f"{BASE}/books/{book['id']}/progress", json={"page": 426})
    assert out.status_code == 422
    assert out.json()["error"]["code"] == "reading.page_out_of_range"


def test_detail_has_weekly_pages(auth_client: TestClient) -> None:
    book = create_book(auth_client)
    with time_machine.travel("2026-10-27T12:00:00Z"):
        progress(auth_client, book["id"], 62)
    with time_machine.travel("2026-11-12T12:00:00Z"):
        progress(auth_client, book["id"], 212)
    detail = auth_client.get(f"{BASE}/books/{book['id']}").json()
    assert detail["weekly_pages"] == [
        {"week_start": "2026-10-26", "pages": 62},
        {"week_start": "2026-11-02", "pages": 0},
        {"week_start": "2026-11-09", "pages": 150},
    ]
    assert detail["pace_pages_per_day"] == round(150 / 14, 1)
    assert detail["forecast_finish_on"] == "2026-12-07"


def test_update_status_dates_and_pages(auth_client: TestClient) -> None:
    book = create_book(auth_client)
    path = f"{BASE}/books/{book['id']}"
    started = auth_client.patch(path, json={"status": "reading"}).json()
    assert (started["status"], started["started_on"], started["current_page"]) == (
        "reading",
        "2026-11-17",
        0,
    )
    progress(auth_client, book["id"], 300)
    fewer = auth_client.patch(path, json={"total_pages": 250})
    assert fewer.json()["error"]["code"] == "reading.page_out_of_range"
    done = auth_client.patch(path, json={"status": "read", "owned": True}).json()
    assert (done["current_page"], done["finished_on"], done["owned"]) == (425, "2026-11-17", True)
    fixed = auth_client.patch(
        path, json={"started_on": "2026-10-26", "finished_on": "2026-11-16", "title": "Clean"}
    ).json()
    assert (fixed["started_on"], fixed["finished_on"], fixed["title"]) == (
        "2026-10-26",
        "2026-11-16",
        "Clean",
    )
    wrong = auth_client.patch(path, json={"finished_on": "2026-10-01"})
    assert wrong.json()["error"]["code"] == "reading.invalid_dates"
    assert auth_client.patch(path, json={"title": None}).status_code == 422


def test_list_filters_search_and_sort(auth_client: TestClient) -> None:
    create_book(auth_client, title="O Hobbit", author="J.R.R. Tolkien", total_pages=336, owned=True)
    create_book(auth_client, current_page=212)
    create_book(auth_client, title="Dom Casmurro", author="Machado de Assis", status="read")

    def titles(**params: str) -> list[str]:
        response = auth_client.get(f"{BASE}/books", params=params)
        assert response.status_code == 200, response.text
        return [item["title"] for item in response.json()["items"]]

    assert titles() == ["Dom Casmurro", "Código Limpo", "O Hobbit"]
    assert titles(sort="title") == ["Código Limpo", "Dom Casmurro", "O Hobbit"]
    assert titles(status="reading") == ["Código Limpo"]
    assert titles(owned="true") == ["O Hobbit"]
    assert titles(owned="false", sort="author") == ["Dom Casmurro", "Código Limpo"]
    assert titles(q="tolk") == ["O Hobbit"]
    assert titles(q="machado") == ["Dom Casmurro"]
    assert titles(q="%") == []
    overview = auth_client.get(f"{BASE}/overview").json()
    assert overview == {
        "books_count": 3,
        "want_to_read_count": 1,
        "reading_count": 1,
        "read_count": 1,
        "notes_count": 0,
    }


def test_delete_book(auth_client: TestClient) -> None:
    book = create_book(auth_client, current_page=10)
    auth_client.post(f"{BASE}/books/{book['id']}/notes", json={"content": "Nota"})
    assert auth_client.delete(f"{BASE}/books/{book['id']}").status_code == 204
    assert auth_client.get(f"{BASE}/books/{book['id']}").status_code == 404
    assert auth_client.get(f"{BASE}/notes").json()["total"] == 0


def test_dashboard_summary_and_activity(auth_client: TestClient) -> None:
    hobbit = create_book(auth_client, title="O Hobbit", author="J.R.R. Tolkien", total_pages=336)
    clean = create_book(auth_client)
    create_book(auth_client, title="Dom Casmurro", author="Machado de Assis", status="read")
    with time_machine.travel("2026-11-15T22:05:00-03:00"):
        progress(auth_client, clean["id"], 198)
        progress(auth_client, clean["id"], 212)
    auth_client.post(
        f"{BASE}/books/{clean['id']}/notes", json={"content": "Funções pequenas.", "page": 98}
    )
    body = auth_client.get("/api/v1/dashboard").json()
    summary = next(m for m in body["modules"] if m["module"] == "reading")
    assert summary["books_count"] == 3
    assert summary["current"]["book"]["title"] == "Código Limpo"
    assert summary["current"]["progress_percent"] == 50
    assert [(s["book"]["title"], s["status"]) for s in summary["shelf"]] == [
        ("Dom Casmurro", "read"),
        ("O Hobbit", "want_to_read"),
    ]
    activity = [item for item in body["activity"] if item["module"] == "reading"]
    kinds = [(item["kind"], item["data"].get("pages")) for item in activity]
    assert ("reading.progress", 14) in kinds
    assert ("reading.progress", 198) in kinds
    note = next(item for item in activity if item["kind"] == "reading.note")
    assert note["data"] == {"page": 98, "excerpt": "Funções pequenas."}
    assert hobbit["id"] not in [item["entity_id"] for item in activity]


def test_other_user_gets_404(auth_client: TestClient, other_client: TestClient) -> None:
    book = create_book(auth_client)
    path = f"{BASE}/books/{book['id']}"
    assert other_client.get(path).status_code == 404
    assert other_client.patch(path, json={"title": "X"}).status_code == 404
    assert other_client.delete(path).status_code == 404
    assert other_client.get(f"{path}/progress").status_code == 404
    assert other_client.post(f"{path}/progress", json={"page": 1}).status_code == 404
    assert other_client.get(f"{path}/notes").status_code == 404
    assert other_client.post(f"{path}/notes", json={"content": "X"}).status_code == 404
    assert other_client.get(f"{path}/cover").status_code == 404
    assert other_client.get(f"{BASE}/books").json()["total"] == 0
