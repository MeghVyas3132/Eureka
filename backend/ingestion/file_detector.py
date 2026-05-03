from enum import Enum
import mimetypes
from typing import cast

from fastapi import HTTPException, UploadFile

try:
    import magic
except ImportError:  # pragma: no cover - fallback when libmagic is unavailable
    magic = None


class FileFormat(str, Enum):
    CSV = "csv"
    EXCEL = "excel"
    PDF = "pdf"


MIME_FORMAT_MAP: dict[str, FileFormat] = {
    "text/csv": FileFormat.CSV,
    "text/plain": FileFormat.CSV,
    "application/csv": FileFormat.CSV,
    "application/vnd.ms-excel": FileFormat.EXCEL,
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": FileFormat.EXCEL,
    "application/pdf": FileFormat.PDF,
}

EXTENSION_FORMAT_MAP: dict[str, FileFormat] = {
    ".csv": FileFormat.CSV,
    ".txt": FileFormat.CSV,
    ".xls": FileFormat.EXCEL,
    ".xlsx": FileFormat.EXCEL,
    ".pdf": FileFormat.PDF,
}

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024


def _detect_mime(file_bytes: bytes, filename: str | None) -> str | None:
    if magic is not None:
        try:
            return cast(str, magic.from_buffer(file_bytes[:2048], mime=True))
        except Exception:
            return None
    if filename:
        guessed, _ = mimetypes.guess_type(filename)
        return guessed
    return None


async def detect_and_validate_file(upload: UploadFile) -> tuple[FileFormat, bytes]:
    file_bytes = await upload.read()

    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=(
                "File too large. Maximum size is 10 MB. "
                f"Received {len(file_bytes) / 1024 / 1024:.1f} MB."
            ),
        )

    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    detected_mime = _detect_mime(file_bytes, upload.filename)
    file_format = MIME_FORMAT_MAP.get(detected_mime or "")

    if file_format is None:
        filename = upload.filename or ""
        ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        file_format = EXTENSION_FORMAT_MAP.get(ext)

    if file_format is None:
        raise HTTPException(
            status_code=415,
            detail=(
                f"Unsupported file type. Detected MIME: {detected_mime}. "
                "Accepted formats: CSV (.csv), Excel (.xlsx, .xls), PDF (.pdf)."
            ),
        )

    return file_format, file_bytes
