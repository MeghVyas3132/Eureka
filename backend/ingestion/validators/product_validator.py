from ingestion.validators.base_validator import RowError, ValidationResult, parse_float

COLUMN_ALIASES = {
    "sku": ["sku", "product_code", "item_code", "barcode", "upc", "product_id"],
    "name": ["name", "product_name", "item_name", "description", "product_description"],
    "brand": ["brand", "brand_name", "manufacturer", "supplier"],
    "category": ["category", "category_name", "dept", "department", "type", "product_type"],
    "width_cm": ["width_cm", "width", "w_cm", "shelf_width", "product_width"],
    "height_cm": ["height_cm", "height", "h_cm", "product_height"],
    "depth_cm": ["depth_cm", "depth", "d_cm", "product_depth"],
    "price": ["price", "unit_price", "retail_price", "selling_price", "rrp", "cost"],
}


def resolve_columns(row: dict) -> dict:
    resolved: dict = {}
    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in row:
                resolved[canonical] = row[alias]
                break
    return resolved


def validate_product_rows(raw_rows: list[dict]) -> ValidationResult:
    valid_rows: list[dict] = []
    error_rows: list[RowError] = []

    for i, raw_row in enumerate(raw_rows):
        row_num = i + 2
        row = resolve_columns(raw_row)
        errors: list[str] = []

        sku = row.get("sku", "").strip().upper()
        name = row.get("name", "").strip()

        if not sku:
            errors.append("sku is required and must not be empty")
        if not name:
            errors.append("name is required and must not be empty")

        if errors:
            error_rows.append(RowError(row=row_num, reason="; ".join(errors), raw_data=raw_row))
            continue

        clean_row: dict = {"sku": sku, "name": name}

        for field_name in ["brand", "category"]:
            val = row.get(field_name, "").strip()
            if val:
                clean_row[field_name] = val

        for float_field in ["width_cm", "height_cm", "depth_cm"]:
            val, err = parse_float(row.get(float_field, ""), float_field)
            if err:
                # Optional field parsing issues are warning-only; do not block row import.
                continue
            if val is not None and val > 0:
                clean_row[float_field] = val

        price_val, price_err = parse_float(row.get("price", ""), "price")
        if not price_err and price_val is not None and price_val >= 0:
            clean_row["price"] = price_val

        if errors:
            error_rows.append(RowError(row=row_num, reason="; ".join(errors), raw_data=raw_row))
        else:
            valid_rows.append(clean_row)

    return ValidationResult(valid_rows=valid_rows, error_rows=error_rows)
