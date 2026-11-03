"""Book covers (R6): validated by content, oriented, reduced and stored as WebP."""

import os
import warnings
from io import BytesIO
from pathlib import Path
from uuid import UUID

from PIL import Image, ImageOps, UnidentifiedImageError

from prumo.core.config import get_settings
from prumo.core.errors import DomainError

MAX_BYTES = 5 * 1024 * 1024
MAX_SIDE = 800
FORMATS = {"JPEG", "PNG", "WEBP"}
MAX_PIXELS = 40_000_000


class CoverTooLargeError(DomainError):
    status_code = 413
    default_code = "reading.cover_too_large"
    default_message = "Cover must be at most 5 MB."


def invalid_cover() -> DomainError:
    return DomainError("Use a JPEG, PNG or WebP image.", code="reading.invalid_cover")


def process(data: bytes) -> bytes:
    """Returns the cover as WebP, at most 800 px on the longer side, without metadata."""
    if len(data) > MAX_BYTES:
        raise CoverTooLargeError(details={"max_bytes": MAX_BYTES})
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as source:
                if source.format not in FORMATS:
                    raise invalid_cover()
                if source.width * source.height > MAX_PIXELS:
                    raise invalid_cover()
                image = ImageOps.exif_transpose(source)
                image.thumbnail((MAX_SIDE, MAX_SIDE))
                has_alpha = image.mode in ("RGBA", "LA") or "transparency" in image.info
                image = image.convert("RGBA" if has_alpha else "RGB")
                output = BytesIO()
                image.save(output, "WEBP", quality=85, method=4)
                return output.getvalue()
    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ) as error:
        raise invalid_cover() from error


def path_for(book_id: UUID) -> Path:
    return get_settings().uploads_dir / "reading" / "covers" / f"{book_id}.webp"


def save(book_id: UUID, webp: bytes) -> None:
    target = path_for(book_id)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".tmp")
    temporary.write_bytes(webp)
    os.replace(temporary, target)


def remove(book_id: UUID) -> None:
    path_for(book_id).unlink(missing_ok=True)
