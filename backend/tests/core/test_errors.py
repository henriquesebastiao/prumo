from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from prumo.core.errors import ConflictError, DomainError, NotFoundError, install_error_handlers


class Item(BaseModel):
    unit_price_cents: int = Field(gt=0)


class Order(BaseModel):
    items: list[Item]


def make_client() -> TestClient:
    app = FastAPI()
    install_error_handlers(app)
    router = APIRouter()

    @router.post("/orders")
    def create_order(order: Order) -> Order:
        return order

    @router.get("/missing")
    def missing() -> None:
        raise NotFoundError()

    @router.get("/rule")
    def rule() -> None:
        raise DomainError(
            "Reading is lower than a previous reading.",
            code="garage.odometer_inconsistent",
            details={"previous_km": 18420},
        )

    @router.get("/conflict")
    def conflict() -> None:
        raise ConflictError(code="finance.category_exists")

    @router.get("/boom")
    def boom() -> None:
        msg = "unexpected"
        raise RuntimeError(msg)

    app.include_router(router)
    return TestClient(app, raise_server_exceptions=False)


def test_validation_error_lists_fields_with_paths() -> None:
    response = make_client().post("/orders", json={"items": [{"unit_price_cents": 0}]})
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert error["fields"] == [
        {
            "path": "items.0.unit_price_cents",
            "code": "greater_than",
            "message": "Input should be greater than 0",
        }
    ]


def test_domain_error_keeps_code_and_details() -> None:
    response = make_client().get("/rule")
    assert response.status_code == 422
    assert response.json() == {
        "error": {
            "code": "garage.odometer_inconsistent",
            "message": "Reading is lower than a previous reading.",
            "details": {"previous_km": 18420},
        }
    }


def test_not_found_and_conflict_statuses() -> None:
    client = make_client()
    assert client.get("/missing").json()["error"]["code"] == "not_found"
    assert client.get("/missing").status_code == 404
    response = client.get("/conflict")
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "finance.category_exists"


def test_framework_errors_use_the_same_format() -> None:
    client = make_client()
    response = client.get("/does-not-exist")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
    response = client.delete("/orders")
    assert response.status_code == 405
    assert response.json()["error"]["code"] == "method_not_allowed"


def test_unexpected_error_is_a_generic_500() -> None:
    response = make_client().get("/boom")
    assert response.status_code == 500
    assert response.json() == {
        "error": {"code": "internal_error", "message": "Internal server error."}
    }
