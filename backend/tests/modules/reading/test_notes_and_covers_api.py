from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from tests.modules.reading.helpers import BASE, create_book, image


def test_notes_crud_and_order(auth_client: TestClient) -> None:
    book = create_book(auth_client)
    path = f"{BASE}/books/{book['id']}/notes"
    first = auth_client.post(
        path, json={"content": "Ir juntando exemplos.", "noted_on": "2026-10-27"}
    )
    assert first.status_code == 201
    assert first.json()["page"] is None
    assert first.json()["book"] == {
        "id": book["id"],
        "title": "Código Limpo",
        "author": "Robert C. Martin",
    }
    today = auth_client.post(path, json={"content": "Tratamento de erros.", "page": 212}).json()
    assert today["noted_on"] == "2026-11-17"
    auth_client.post(
        path, json={"content": "Objetos e estruturas.", "page": 176, "noted_on": "2026-11-10"}
    )

    items = auth_client.get(path).json()["items"]
    assert [item["noted_on"] for item in items] == ["2026-11-17", "2026-11-10", "2026-10-27"]
    assert auth_client.get(f"{BASE}/books/{book['id']}").json()["notes_count"] == 3

    note_path = f"{path}/{today['id']}"
    edited = auth_client.patch(note_path, json={"content": "Erros: exceções.", "page": None})
    assert edited.json()["content"] == "Erros: exceções."
    assert edited.json()["page"] is None
    assert auth_client.patch(note_path, json={"noted_on": None}).status_code == 422
    beyond = auth_client.patch(note_path, json={"page": 500})
    assert beyond.json()["error"]["code"] == "reading.page_out_of_range"
    assert auth_client.post(path, json={"content": "  "}).status_code == 422
    assert auth_client.delete(note_path).status_code == 204
    assert auth_client.patch(note_path, json={"content": "X"}).status_code == 404


def test_all_notes_with_search(auth_client: TestClient) -> None:
    clean = create_book(auth_client)
    casmurro = create_book(auth_client, title="Dom Casmurro", author="Machado de Assis")
    auth_client.post(f"{BASE}/books/{clean['id']}/notes", json={"content": "Funções pequenas."})
    auth_client.post(
        f"{BASE}/books/{casmurro['id']}/notes",
        json={"content": "Olhos de ressaca.", "noted_on": "2026-10-01"},
    )
    body = auth_client.get(f"{BASE}/notes").json()
    assert body["total"] == 2
    assert [item["book"]["title"] for item in body["items"]] == ["Código Limpo", "Dom Casmurro"]
    found = auth_client.get(f"{BASE}/notes", params={"q": "RESSACA"}).json()
    assert [item["content"] for item in found["items"]] == ["Olhos de ressaca."]
    assert auth_client.get(f"{BASE}/overview").json()["notes_count"] == 2


def test_cover_is_reduced_and_stored_as_webp(auth_client: TestClient, uploads: Path) -> None:
    book = create_book(auth_client)
    path = f"{BASE}/books/{book['id']}/cover"
    assert auth_client.get(path).status_code == 404
    response = auth_client.put(path, files={"file": ("capa.png", image(), "image/png")})
    assert response.status_code == 200, response.text
    assert response.json()["has_cover"] is True
    stored = uploads / "reading" / "covers" / f"{book['id']}.webp"
    assert stored.is_file()

    served = auth_client.get(path)
    assert served.status_code == 200
    assert served.headers["content-type"] == "image/webp"
    with Image.open(BytesIO(served.content)) as cover:
        assert cover.format == "WEBP"
        assert cover.size == (800, 600)

    jpeg = auth_client.put(
        path, files={"file": ("capa.jpg", image("JPEG", (300, 400)), "image/jpeg")}
    )
    assert jpeg.status_code == 200
    with Image.open(BytesIO(auth_client.get(path).content)) as cover:
        assert cover.size == (300, 400)  # never enlarged

    assert auth_client.delete(path).status_code == 204
    assert not stored.exists()
    assert auth_client.get(path).status_code == 404
    assert auth_client.get(f"{BASE}/books/{book['id']}").json()["has_cover"] is False


def test_cover_validation(auth_client: TestClient) -> None:
    book = create_book(auth_client)
    path = f"{BASE}/books/{book['id']}/cover"
    text = auth_client.put(path, files={"file": ("capa.png", b"not an image", "image/png")})
    assert text.status_code == 422
    assert text.json()["error"]["code"] == "reading.invalid_cover"
    gif = auth_client.put(path, files={"file": ("capa.gif", image("GIF", (10, 10)), "image/gif")})
    assert gif.json()["error"]["code"] == "reading.invalid_cover"
    big = auth_client.put(
        path, files={"file": ("capa.png", b"\x89PNG" + b"0" * (5 * 1024 * 1024), "image/png")}
    )
    assert big.status_code == 413
    assert big.json()["error"]["code"] == "reading.cover_too_large"


def test_deleting_the_book_removes_the_cover(auth_client: TestClient, uploads: Path) -> None:
    book = create_book(auth_client)
    auth_client.put(
        f"{BASE}/books/{book['id']}/cover", files={"file": ("c.png", image(), "image/png")}
    )
    auth_client.delete(f"{BASE}/books/{book['id']}")
    assert not (uploads / "reading" / "covers" / f"{book['id']}.webp").exists()


def test_other_user_gets_404(auth_client: TestClient, other_client: TestClient) -> None:
    book = create_book(auth_client)
    note = auth_client.post(f"{BASE}/books/{book['id']}/notes", json={"content": "Minha"}).json()
    note_path = f"{BASE}/books/{book['id']}/notes/{note['id']}"
    assert other_client.patch(note_path, json={"content": "X"}).status_code == 404
    assert other_client.delete(note_path).status_code == 404
    cover = f"{BASE}/books/{book['id']}/cover"
    assert (
        other_client.put(cover, files={"file": ("c.png", image(), "image/png")}).status_code == 404
    )
    assert other_client.delete(cover).status_code == 404
    assert other_client.get(f"{BASE}/notes").json()["total"] == 0
    # A note of another book of the same user is not reachable through this book.
    other_book = create_book(auth_client, title="Outro")
    assert (
        auth_client.delete(f"{BASE}/books/{other_book['id']}/notes/{note['id']}").status_code == 404
    )
