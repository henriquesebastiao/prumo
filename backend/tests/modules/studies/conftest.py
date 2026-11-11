from collections.abc import Iterator

import pytest
import time_machine

NOW = "2026-11-17T17:30:00Z"  # Tuesday 14:30 in São Paulo, like the design boards


@pytest.fixture(autouse=True)
def design_clock() -> Iterator[None]:
    """Studies rules depend on "today"; tests run at the moment of the design boards."""
    with time_machine.travel(NOW, tick=True):
        yield
