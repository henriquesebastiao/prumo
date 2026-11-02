from collections.abc import Iterator

import pytest
from sqlalchemy.orm import Session

from prumo.core.errors import ConflictError, DomainError
from prumo.core.security import verify_password
from prumo.main import bootstrap
from prumo.system.preferences.service import enabled_module_ids, get_preferences
from prumo.system.users import service
from prumo.system.users.schemas import UserUpdate
from tests.fakes.modules import journal, notes, tasks


@pytest.fixture
def fake_modules() -> Iterator[None]:
    bootstrap([tasks, notes])
    journal.clear()
    yield
    journal.clear()
    bootstrap()


def test_create_user_normalizes_username_and_hashes_password(db: Session) -> None:
    user = service.create_user(
        db, username="  Ana.Souza ", display_name=" Ana ", password="senha-segura-123"
    )
    assert user.username == "ana.souza"
    assert user.display_name == "Ana"
    assert not user.is_admin
    assert verify_password(user.password_hash, "senha-segura-123")
    assert service.get_by_username(db, "ANA.SOUZA") is user


def test_create_user_creates_default_preferences_and_runs_module_hooks(
    db: Session, fake_modules: None
) -> None:
    user = service.create_user(db, username="ana", display_name="Ana", password="senha-123456")
    preferences = get_preferences(db, user.id)
    assert preferences.theme == "system"
    assert preferences.locale == "pt-BR"
    assert preferences.timezone == "America/Sao_Paulo"
    assert preferences.currency == "BRL"
    assert enabled_module_ids(preferences) == ["tasks", "notes"]
    assert journal.created_users == ["ana"]


@pytest.mark.parametrize(
    ("username", "password", "code"),
    [
        ("a", "senha-segura-123", "users.invalid_username"),
        ("ana souza", "senha-segura-123", "users.invalid_username"),
        ("-ana", "senha-segura-123", "users.invalid_username"),
        ("ana", "curta", "users.password_too_short"),
        ("ana", "x" * 129, "users.password_too_long"),
    ],
)
def test_create_user_validates_input(db: Session, username: str, password: str, code: str) -> None:
    with pytest.raises(DomainError) as error:
        service.create_user(db, username=username, display_name="Ana", password=password)
    assert error.value.code == code


def test_username_is_unique_ignoring_case(db: Session) -> None:
    service.create_user(db, username="ana", display_name="Ana", password="senha-segura-123")
    with pytest.raises(ConflictError) as error:
        service.create_user(db, username="ANA", display_name="Outra", password="senha-segura-123")
    assert error.value.code == "users.username_taken"


def test_set_password_and_update_profile(db: Session) -> None:
    user = service.create_user(db, username="ana", display_name="Ana", password="senha-segura-123")
    service.set_password(db, user, "nova-senha-456")
    assert verify_password(user.password_hash, "nova-senha-456")
    service.update_profile(db, user, UserUpdate(display_name="Ana Souza"))
    assert user.display_name == "Ana Souza"
