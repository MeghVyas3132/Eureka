from ingestion.validators.product_validator import validate_product_rows
from ingestion.validators.sales_validator import validate_sales_rows


def test_product_validator_valid_row():
    raw_rows = [
        {
            "sku": "sku-1",
            "name": "Sample",
            "width_cm": "10",
            "height_cm": "5",
            "depth_cm": "2",
            "price": "1.99",
        }
    ]

    result = validate_product_rows(raw_rows)

    assert len(result.valid_rows) == 1
    assert result.valid_rows[0]["sku"] == "SKU-1"


def test_product_validator_missing_required_fields():
    raw_rows = [{"sku": "", "name": ""}]

    result = validate_product_rows(raw_rows)

    assert len(result.error_rows) == 1
    assert "sku is required" in result.error_rows[0].reason


def test_product_validator_invalid_numeric():
    raw_rows = [{"sku": "SKU-1", "name": "Sample", "width_cm": "abc"}]

    result = validate_product_rows(raw_rows)

    assert len(result.error_rows) == 1
    assert "width_cm must be a number" in result.error_rows[0].reason


def test_product_validator_negative_price():
    raw_rows = [{"sku": "SKU-1", "name": "Sample", "price": "-1"}]

    result = validate_product_rows(raw_rows)

    assert len(result.error_rows) == 1
    assert "price must be >= 0" in result.error_rows[0].reason


def test_product_validator_flexible_columns():
    raw_rows = [{"product_code": "SKU-9", "product_name": "Flexible"}]

    result = validate_product_rows(raw_rows)

    assert len(result.valid_rows) == 1
    assert result.valid_rows[0]["sku"] == "SKU-9"


def test_sales_validator_with_override_period():
    raw_rows = [{"sku": "SKU-1", "revenue": "10"}]

    result = validate_sales_rows(raw_rows, "2025-01-01", "2025-01-31")

    assert len(result.valid_rows) == 1
    assert result.valid_rows[0]["period_start"] == "2025-01-01"


def test_sales_validator_missing_revenue():
    raw_rows = [{"sku": "SKU-1"}]

    result = validate_sales_rows(raw_rows, "2025-01-01", "2025-01-31")

    assert len(result.error_rows) == 1
    assert "revenue is required" in result.error_rows[0].reason


def test_sales_validator_negative_units():
    raw_rows = [{"sku": "SKU-1", "revenue": "10", "units_sold": "-1"}]

    result = validate_sales_rows(raw_rows, "2025-01-01", "2025-01-31")

    assert len(result.error_rows) == 1
    assert "units_sold must be >= 0" in result.error_rows[0].reason


def test_sales_validator_period_end_before_start():
    raw_rows = [{"sku": "SKU-1", "revenue": "10", "period_start": "2025-02-01", "period_end": "2025-01-01"}]

    result = validate_sales_rows(raw_rows, None, None)

    assert len(result.error_rows) == 1
    assert "period_end" in result.error_rows[0].reason
