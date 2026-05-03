import io

import pandas as pd
import pytest
from fastapi import HTTPException, UploadFile
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from ingestion.file_detector import FileFormat, detect_and_validate_file


def _make_upload(filename: str, content: bytes) -> UploadFile:
    return UploadFile(filename=filename, file=io.BytesIO(content))


def _xlsx_bytes() -> bytes:
    buffer = io.BytesIO()
    df = pd.DataFrame([{"sku": "SKU-1", "name": "Test"}])
    df.to_excel(buffer, index=False, engine="openpyxl")
    return buffer.getvalue()


def _pdf_bytes() -> bytes:
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.drawString(72, 720, "SKU  Revenue")
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


@pytest.mark.anyio
async def test_detect_csv_bytes():
    content = b"sku,name\nSKU-1,Sample\n"
    upload = _make_upload("products.csv", content)

    file_format, file_bytes = await detect_and_validate_file(upload)

    assert file_format == FileFormat.CSV
    assert file_bytes == content


@pytest.mark.anyio
async def test_detect_xlsx_bytes():
    content = _xlsx_bytes()
    upload = _make_upload("products.xlsx", content)

    file_format, _ = await detect_and_validate_file(upload)

    assert file_format == FileFormat.EXCEL


@pytest.mark.anyio
async def test_detect_pdf_bytes():
    content = _pdf_bytes()
    upload = _make_upload("sales.pdf", content)

    file_format, _ = await detect_and_validate_file(upload)

    assert file_format == FileFormat.PDF


@pytest.mark.anyio
async def test_rejects_large_file():
    content = b"a" * (10 * 1024 * 1024 + 1)
    upload = _make_upload("large.csv", content)

    with pytest.raises(HTTPException) as exc:
        await detect_and_validate_file(upload)

    assert exc.value.status_code == 413


@pytest.mark.anyio
async def test_rejects_empty_file():
    upload = _make_upload("empty.csv", b"")

    with pytest.raises(HTTPException) as exc:
        await detect_and_validate_file(upload)

    assert exc.value.status_code == 400


@pytest.mark.anyio
async def test_rejects_unsupported_file():
    content = b"\x89PNG\r\n\x1a\n" + b"0" * 100
    upload = _make_upload("image.png", content)

    with pytest.raises(HTTPException) as exc:
        await detect_and_validate_file(upload)

    assert exc.value.status_code == 415


@pytest.mark.anyio
async def test_detects_csv_with_bom():
    content = b"\xef\xbb\xbfsku,name\nSKU-1,Sample\n"
    upload = _make_upload("bom.csv", content)

    file_format, _ = await detect_and_validate_file(upload)

    assert file_format == FileFormat.CSV


@pytest.mark.anyio
async def test_detects_txt_as_csv():
    content = b"sku,name\nSKU-1,Sample\n"
    upload = _make_upload("products.txt", content)

    file_format, _ = await detect_and_validate_file(upload)

    assert file_format == FileFormat.CSV
