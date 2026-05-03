from ingestion.validators.base_validator import RowError, ValidationResult, parse_date, parse_float, parse_int

COLUMN_ALIASES = {
    "sku": ["sku", "product_code", "item_code", "barcode", "upc", "product_id"],
    "units_sold": ["units_sold", "units", "qty", "quantity", "quantity_sold", "sales_qty", "volume"],
    "revenue": [
        "revenue",
        "sales",
        "total_sales",
        "net_sales",
        "gross_sales",
        "amount",
        "value",
        "total",
    ],
    "period_start": ["period_start", "start_date", "from_date", "date_from", "week_start", "start"],
    "period_end": ["period_end", "end_date", "to_date", "date_to", "week_end", "end"],
}


def resolve_columns(row: dict) -> dict:
    resolved: dict = {}
    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in row:
                resolved[canonical] = row[alias]
                break
    return resolved


def validate_sales_rows(
    raw_rows: list[dict],
    period_start_override: str | None,
    period_end_override: str | None,
) -> ValidationResult:
    valid_rows: list[dict] = []
    error_rows: list[RowError] = []

    for i, raw_row in enumerate(raw_rows):
        row_num = i + 2
        row = resolve_columns(raw_row)
        errors: list[str] = []

        sku = row.get("sku", "").strip().upper()
        if not sku:
            error_rows.append(RowError(row=row_num, reason="sku is required and must not be empty", raw_data=raw_row))
            continue

        revenue_val, revenue_err = parse_float(row.get("revenue", ""), "revenue")
        if revenue_err:
            errors.append(revenue_err)
        elif revenue_val is None:
            errors.append("revenue is required")
        elif revenue_val < 0:
            errors.append(f"revenue must be >= 0, got {revenue_val}")

        units_val, units_err = parse_int(row.get("units_sold", ""), "units_sold")
        if units_err:
            errors.append(units_err)
        elif units_val is not None and units_val < 0:
            errors.append(f"units_sold must be >= 0, got {units_val}")

        if period_start_override:
            period_start = period_start_override
        else:
            period_start, ps_err = parse_date(row.get("period_start", ""), "period_start")
            if ps_err:
                errors.append(ps_err)
            elif not period_start:
                errors.append("period_start is required (provide as query param or in each row)")

        if period_end_override:
            period_end = period_end_override
        else:
            period_end, pe_err = parse_date(row.get("period_end", ""), "period_end")
            if pe_err:
                errors.append(pe_err)
            elif not period_end:
                errors.append("period_end is required (provide as query param or in each row)")

        if period_start and period_end and period_end < period_start:
            errors.append(f"period_end ({period_end}) must be >= period_start ({period_start})")

        if errors:
            error_rows.append(RowError(row=row_num, reason="; ".join(errors), raw_data=raw_row))
        else:
            clean_row: dict = {
                "sku": sku,
                "revenue": revenue_val,
                "period_start": period_start,
                "period_end": period_end,
                "ingestion_method": "file_import",
            }
            if units_val is not None:
                clean_row["units_sold"] = units_val
            valid_rows.append(clean_row)

    return ValidationResult(valid_rows=valid_rows, error_rows=error_rows)
