from collections.abc import Callable, Iterator, Sequence
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session

from prumo.core.db import get_session
from prumo.core.modules import PrumoModule
from prumo.main import bootstrap, create_app
from prumo.system.users.models import User
from tests import factories

BACKEND_DIR = Path(__file__).resolve().parents[1]


class TestDatabaseSettings(BaseSettings):
    """`PRUMO_TEST_DATABASE_URL`: the throwaway database from docker-compose.dev.yml (or CI)."""

    model_config = SettingsConfigDict(
        env_prefix="PRUMO_TEST_", env_file=("../.env", ".env"), extra="ignore"
    )

    database_url: str = "postgresql+psycopg://prumo:prumo@localhost:5433/prumo_test"


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    """Recreates the test schema from the migrations, so they are exercised on every run."""
    engine = create_engine(TestDatabaseSettings().database_url)
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))
    config = Config(BACKEND_DIR / "alembic.ini")
    config.attributes["configure_logger"] = False
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
    yield engine
    engine.dispose()


@pytest.fixture
def db(engine: Engine) -> Iterator[Session]:
    """A session inside a transaction that is rolled back after the test. `commit()` in the code
    under test only releases a savepoint."""
    with engine.connect() as connection:
        transaction = connection.begin()
        session = Session(
            bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False
        )
        try:
            yield session
        finally:
            session.close()
            transaction.rollback()


type AppFactory = Callable[[Sequence[PrumoModule] | None], FastAPI]


@pytest.fixture
def make_app(db: Session) -> Iterator[AppFactory]:
    """Builds an app bound to the test session, optionally with fake modules installed."""

    def factory(modules: Sequence[PrumoModule] | None = None) -> FastAPI:
        app = create_app(modules)
        app.dependency_overrides[get_session] = lambda: db
        return app

    yield factory
    bootstrap()  # back to the real INSTALLED_MODULES


@pytest.fixture
def app(make_app: AppFactory) -> FastAPI:
    return make_app(None)


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app, base_url="https://testserver") as test_client:
        yield test_client


@pytest.fixture
def user(db: Session, app: FastAPI) -> User:
    return factories.create_user(db, username="ana", display_name="Ana Souza")


@pytest.fixture
def other_user(db: Session, app: FastAPI) -> User:
    return factories.create_user(db, username="bruno", display_name="Bruno Lima")


@pytest.fixture
def auth_client(client: TestClient, db: Session, user: User) -> TestClient:
    """Client authenticated as `user` with an app (bearer) session."""
    client.headers["Authorization"] = f"Bearer {factories.create_session_token(db, user)}"
    return client


@pytest.fixture
def other_client(app: FastAPI, db: Session, other_user: User) -> Iterator[TestClient]:
    """A second client, authenticated as `other_user`."""
    with TestClient(app, base_url="https://testserver") as test_client:
        token = factories.create_session_token(db, other_user)
        test_client.headers["Authorization"] = f"Bearer {token}"
        yield test_client
