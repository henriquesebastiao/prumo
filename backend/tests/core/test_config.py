import pytest

from prumo.core.config import Settings


def test_cors_origins_are_comma_separated(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PRUMO_CORS_ORIGINS", "https://a.example, https://b.example,")
    assert Settings().cors_origins == ["https://a.example", "https://b.example"]


def test_empty_cors_origins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PRUMO_CORS_ORIGINS", "")
    assert Settings().cors_origins == []
