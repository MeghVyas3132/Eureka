import io
from pathlib import Path

import pandas as pd
import pytest
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

from ingestion.parsers.csv_parser import CSVParser
from ingestion.parsers.excel_parser import ExcelParser
from ingestion.parsers.pdf_parser import PDFParser

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"


def _read_fixture(name: str) -> bytes:
    return (FIXTURES_DIR / name).read_bytes()


def _xlsx_bytes() -> bytes:
    buffer = io.BytesIO()
    df = pd.DataFrame(
        [
            {"sku": "SKU-1", "name": "Sample", "price": 1.5},
            {"sku": "SKU-2", "name": "Sample 2", "price": 2.5},
        ]
    )
    df.to_excel(buffer, index=False, engine="openpyxl")
    return buffer.getvalue()


def _xls_bytes() -> bytes:
    buffer = io.BytesIO()
    df = pd.DataFrame([{"sku": "SKU-1", "name": "Legacy", "price": 3.5}])
    df.to_excel(buffer, index=False, engine="xlwt")
    return buffer.getvalue()


def _pdf_table_bytes() -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    data = [
        ["sku", "revenue"],
        ["SKU-1", "100"],
        ["SKU-2", "200"],
    ]
    table = Table(data)
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ]
        )
    )
    doc.build([table])
    return buffer.getvalue()


def _pdf_text_only_bytes() -> bytes:
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.drawString(72, 720, "No tables here")
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def test_csv_parser_standard():
    parser = CSVParser()
    rows = parser.parse(_read_fixture("products_valid.csv"))

    assert len(rows) == 5
    assert rows[0]["sku"] == "SKU-001"


def test_csv_parser_bom():
    parser = CSVParser()
    content = b"\xef\xbb\xbfsku,name\nSKU-1,Sample\n"

    rows = parser.parse(content)

    assert len(rows) == 1
    assert rows[0]["sku"] == "SKU-1"


def test_csv_parser_latin1():
    parser = CSVParser()
    content = "sku,name\nSKU-1,Caf\u00e9\n".encode("latin-1")

    rows = parser.parse(content)

    assert rows[0]["name"] == "Caf\u00e9"


def test_csv_parser_blank_rows_skipped():
    parser = CSVParser()
    content = b"sku,name\nSKU-1,Sample\n\n\nSKU-2,Sample 2\n"

    rows = parser.parse(content)

    assert len(rows) == 2


def test_csv_parser_header_only():
    parser = CSVParser()
    rows = parser.parse(_read_fixture("header_only.csv"))

    assert rows == []


def test_csv_parser_trailing_commas():
    parser = CSVParser()
    content = b"sku,name,brand,\nSKU-1,Sample,Brand,\n"

    rows = parser.parse(content)

    assert rows[0]["brand"] == "Brand"


def test_excel_parser_xlsx():
    parser = ExcelParser()
    rows = parser.parse(_xlsx_bytes())

    assert len(rows) == 2
    assert rows[0]["sku"] == "SKU-1"


def test_excel_parser_xls():
    parser = ExcelParser()
    try:
        content = _xls_bytes()
    except Exception:
        pytest.skip("xls generation unavailable")

    rows = parser.parse(content)

    assert len(rows) == 1
    assert rows[0]["sku"] == "SKU-1"


def test_excel_parser_numeric_sku_to_string():
    parser = ExcelParser()
    buffer = io.BytesIO()
    df = pd.DataFrame([{"sku": 12345, "name": "Numeric"}])
    df.to_excel(buffer, index=False, engine="openpyxl")

    rows = parser.parse(buffer.getvalue())

    assert rows[0]["sku"] == "12345"


def test_excel_parser_nan_replaced():
    parser = ExcelParser()
    buffer = io.BytesIO()
    df = pd.DataFrame([{"sku": "SKU-1", "name": None}])
    df.to_excel(buffer, index=False, engine="openpyxl")

    rows = parser.parse(buffer.getvalue())

    assert rows[0]["name"] == ""


def test_pdf_parser_table():
    parser = PDFParser()

    rows = parser.parse(_pdf_table_bytes())

    assert len(rows) == 2
    assert rows[0]["sku"] == "SKU-1"


def test_pdf_parser_no_table():
    parser = PDFParser()

    with pytest.raises(ValueError):
        parser.parse(_pdf_text_only_bytes())
