from ingestion.validators.base_validator import RowError, ValidationResult

COLUMN_ALIASES = {
    "store_name": ["store_name", "store", "outlet", "branch", "location_name", "name"],
    "city": ["city", "town", "location"],
    "state": ["state", "province", "region"],
    "store_type": ["store_type", "format", "type", "outlet_type"],
}


def resolve_columns(row: dict) -> dict:
    resolved: dict = {}
    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in row:
                resolved[canonical] = row[alias]
                break
    return resolved


def validate_store_rows(raw_rows: list[dict]) -> ValidationResult:
    valid_rows: list[dict] = []
    error_rows: list[RowError] = []

    for i, raw_row in enumerate(raw_rows):
        row_num = i + 2
        row = resolve_columns(raw_row)

        store_name = str(row.get("store_name", "") or "").strip()
        if not store_name:
            error_rows.append(
                RowError(row=row_num, reason="store_name is required and must not be empty", raw_data=raw_row)
            )
            continue

        clean_row: dict = {
            "name": store_name,
            "raw_name": store_name,
        }

        city = str(row.get("city", "") or "").strip()
        state = str(row.get("state", "") or "").strip()
        store_type = str(row.get("store_type", "") or "").strip().lower()

        if city:
            clean_row["city"] = city.title()
        if state:
            clean_row["state"] = state.title()
        if store_type:
            clean_row["store_type"] = store_type

        valid_rows.append(clean_row)

    return ValidationResult(valid_rows=valid_rows, error_rows=error_rows)
