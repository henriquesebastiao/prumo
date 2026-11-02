import io
import json
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from prumo import cli
from prumo.core.security import verify_password
from prumo.system.users.service import get_by_username


@pytest.fixture(autouse=True)
def cli_uses_test_session(db: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    class _Factory:
        def __call__(self) -> _Factory:
            return self

        def __enter__(self) -> Session:
            return db

        def __exit__(self, *args: object) -> None:
            return None

    monkeypatch.setattr(cli, "get_sessionmaker", lambda: _Factory())


def test_create_user_from_arguments_and_stdin(
    db: Session, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO("senha-segura-123\n"))
    code = cli.main(
        [
            "users",
            "create",
            "--username",
            "Ana",
            "--name",
            "Ana Souza",
            "--admin",
            "--password-stdin",
        ]
    )
    assert code == 0
    assert "Criado administrador 'ana'" in capsys.readouterr().out
    user = get_by_username(db, "ana")
    assert user is not None
    assert user.is_admin
    assert verify_password(user.password_hash, "senha-segura-123")


def test_create_user_interactively(db: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    answers = iter(["bruno", "Bruno Lima"])
    passwords = iter(["senha-segura-123", "senha-segura-123"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))
    monkeypatch.setattr("getpass.getpass", lambda prompt: next(passwords))
    assert cli.main(["users", "create"]) == 0
    assert get_by_username(db, "bruno") is not None


def test_domain_errors_become_exit_code_1(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO("curta\n"))
    code = cli.main(["users", "create", "--username", "ana", "--name", "Ana", "--password-stdin"])
    assert code == 1
    assert "users.password_too_short" in capsys.readouterr().err


def test_set_password(db: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO("senha-segura-123\n"))
    cli.main(["users", "create", "--username", "ana", "--name", "Ana", "--password-stdin"])
    monkeypatch.setattr("sys.stdin", io.StringIO("nova-senha-456\n"))
    assert cli.main(["users", "set-password", "ana", "--password-stdin"]) == 0
    user = get_by_username(db, "ana")
    assert user is not None
    assert verify_password(user.password_hash, "nova-senha-456")
    assert cli.main(["users", "set-password", "ninguem", "--password-stdin"]) == 1


def test_openapi_export(tmp_path: Path) -> None:
    target = tmp_path / "openapi.json"
    assert cli.main(["openapi", str(target)]) == 0
    assert json.loads(target.read_text())["info"]["title"] == "Prumo API"
