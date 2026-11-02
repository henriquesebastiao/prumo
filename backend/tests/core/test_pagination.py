from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from prumo.core.errors import install_error_handlers
from prumo.core.pagination import Page, PageDep, PageParams, Sort, paginate, sort_param
from prumo.system.users.models import User
from tests import factories

UserSort = Annotated[Sort, Depends(sort_param("username", "created_at", default="username"))]


def make_client() -> TestClient:
    app = FastAPI()
    install_error_handlers(app)
    router = APIRouter()

    @router.get("/items")
    def list_items(page: PageDep, sort: UserSort) -> dict[str, object]:
        return {"limit": page.limit, "offset": page.offset, "sort": sort.token}

    app.include_router(router)
    return TestClient(app)


def test_page_params_defaults_and_bounds() -> None:
    client = make_client()
    assert client.get("/items").json() == {"limit": 50, "offset": 0, "sort": "username"}
    assert client.get("/items?limit=200&offset=10&sort=-created_at").json() == {
        "limit": 200,
        "offset": 10,
        "sort": "-created_at",
    }
    for query in ("limit=0", "limit=201", "offset=-1"):
        response = client.get(f"/items?{query}")
        assert response.status_code == 422, query


def test_unknown_sort_field_is_a_validation_error() -> None:
    response = make_client().get("/items?sort=password_hash")
    assert response.status_code == 422
    field = response.json()["error"]["fields"][0]
    assert field["path"] == "sort"
    assert field["code"] == "enum"


def test_paginate_counts_sorts_and_slices(db: Session) -> None:
    for name in ("carla", "ana", "bruno"):
        factories.create_user(db, username=name, display_name=name.title())

    page: Page[User] = paginate(
        db,
        select(User),
        PageParams(limit=2, offset=0),
        sort=Sort(field="username", descending=True),
        sort_columns={"username": User.username},
        tiebreaker=(User.id,),
    )
    assert page.total == 3
    assert [user.username for user in page.items] == ["carla", "bruno"]

    second: Page[User] = paginate(
        db,
        select(User),
        PageParams(limit=2, offset=2),
        sort=Sort(field="username", descending=True),
        sort_columns={"username": User.username},
    )
    assert [user.username for user in second.items] == ["ana"]
    assert second.limit == 2
    assert second.offset == 2
