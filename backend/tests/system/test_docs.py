from fastapi.testclient import TestClient


def test_docs_are_served_by_the_instance(client: TestClient) -> None:
    page = client.get("/api/docs")
    assert page.status_code == 200
    assert "/api/docs/static/swagger-ui-bundle.js" in page.text
    assert "/api/openapi.json" in page.text
    assert "cdn.jsdelivr.net" not in page.text
    script = client.get("/api/docs/static/swagger-ui-bundle.js")
    assert script.status_code == 200
    assert "javascript" in script.headers["content-type"]
    assert client.get("/api/docs/static/swagger-ui.css").status_code == 200
    assert client.get("/api/docs/static/missing.js").status_code == 404
