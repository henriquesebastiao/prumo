from collections.abc import Iterator
from pathlib import Path

import pytest
import time_machine

from prumo.core.config import get_settings

NOW = "2026-11-17T17:30:00Z"  # Tuesday 14:30 in São Paulo, like the design boards


@pytest.fixture(autouse=True)
def design_clock() -> Iterator[None]:
    """Reading rules depend on "today"; tests run at the moment of the design boards."""
    with time_machine.travel(NOW, tick=True):
        yield


@pytest.fixture(autouse=True)
def uploads(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(get_settings(), "uploads_dir", tmp_path)
    return tmp_path
