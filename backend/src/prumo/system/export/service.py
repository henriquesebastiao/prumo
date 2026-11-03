"""User data export (D38): a ZIP with data.json, one CSV per table and the uploaded files."""

import csv
import io
import json
import zipfile
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from prumo import __version__
from prumo.core.clock import utcnow
from prumo.core.export import ExportTable, plain
from prumo.core.modules import registry
from prumo.system.preferences.service import enabled_module_ids, get_preferences
from prumo.system.users.models import User

FORMAT = "prumo-export"
FORMAT_VERSION = 1


def _csv(table: ExportTable) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(table.columns), lineterminator="\n")
    writer.writeheader()
    writer.writerows(table.rows)
    return output.getvalue()


def filename(user: User, now: datetime) -> str:
    return f"prumo-{user.username}-{now:%Y%m%d-%H%M}.zip"


def build_archive(session: Session, user: User) -> tuple[str, bytes]:
    """The archive and its file name. Passwords, sessions and login attempts are never included."""
    now = utcnow()
    preferences = get_preferences(session, user.id)
    data: dict[str, Any] = {
        "format": FORMAT,
        "format_version": FORMAT_VERSION,
        "app_version": __version__,
        "exported_at": now.isoformat(),
        "user": {
            "id": str(user.id),
            "username": user.username,
            "display_name": user.display_name,
            "created_at": plain(user.created_at),
        },
        "preferences": {
            "theme": plain(preferences.theme),
            "locale": preferences.locale,
            "timezone": preferences.timezone,
            "currency": preferences.currency,
            "enabled_modules": enabled_module_ids(preferences),
        },
        "modules": {},
    }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for module in registry.modules:
            if module.export is None:
                continue
            exported = module.export(session, user)
            data["modules"][module.id] = {
                name: list(table.rows) for name, table in exported.tables.items()
            }
            for name, table in exported.tables.items():
                archive.writestr(f"{module.id}/{name}.csv", _csv(table))
            for path, source in exported.files.items():
                archive.write(source, f"{module.id}/{path}")
        archive.writestr(
            "data.json", json.dumps(data, ensure_ascii=False, indent=2, sort_keys=False)
        )
    return filename(user, now), buffer.getvalue()
