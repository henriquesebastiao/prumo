"""Helpers that create reading records through the API, like a client would."""

from io import BytesIO
from typing import Any

from fastapi.testclient import TestClient
from PIL import Image

BASE = "/api/v1/reading"


def create_book(client: TestClient, **overrides: Any) -> dict[str, Any]:
    payload = {"title": "Código Limpo", "author": "Robert C. Martin", "total_pages": 425}
    response = client.post(f"{BASE}/books", json=payload | overrides)
    assert response.status_code == 201, response.text
    body: dict[str, Any] = response.json()
    return body


def progress(client: TestClient, book_id: str, page: int) -> dict[str, Any]:
    response = client.post(f"{BASE}/books/{book_id}/progress", json={"page": page})
    assert response.status_code == 201, response.text
    body: dict[str, Any] = response.json()
    return body


def image(fmt: str = "PNG", size: tuple[int, int] = (1600, 1200)) -> bytes:
    output = BytesIO()
    Image.new("RGB", size, (111, 87, 232)).save(output, fmt)
    return output.getvalue()
