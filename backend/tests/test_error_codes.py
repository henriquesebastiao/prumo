"""Every error code the API can answer is documented (docs/api.md) and translated by the web
(frontend/src/app/locales/pt-BR.json, `errors.<code>`)."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "backend" / "src" / "prumo"
DOCS = ROOT / "docs" / "api.md"
LOCALE = ROOT / "frontend" / "src" / "app" / "locales" / "pt-BR.json"
PATTERNS = (re.compile(r'code="([a-z_.]+)"'), re.compile(r'default_code = "([a-z_.]+)"'))
# Generic codes of the error handlers, documented in the status table.
HANDLER_CODES = {"domain_error", "internal_error", "http_error", "method_not_allowed"}


def api_codes() -> set[str]:
    codes: set[str] = set()
    for path in SOURCE.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for pattern in PATTERNS:
            codes.update(pattern.findall(text))
    return codes - HANDLER_CODES


def translated(messages: dict[str, object], code: str) -> bool:
    node: object = messages
    for part in code.split("."):
        if not isinstance(node, dict) or part not in node:
            return False
        node = node[part]
    return isinstance(node, str)


def test_error_codes_are_documented_and_translated() -> None:
    codes = api_codes()
    assert "finance.category_in_use" in codes  # the scan works
    docs = DOCS.read_text(encoding="utf-8")
    errors = json.loads(LOCALE.read_text(encoding="utf-8"))["errors"]
    assert sorted(c for c in codes if f"`{c}`" not in docs) == []
    assert sorted(c for c in codes if not translated(errors, c)) == []
