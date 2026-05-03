from dataclasses import dataclass, field


@dataclass
class RowError:
    row: int
    reason: str
    raw_data: dict = field(default_factory=dict)


@dataclass
class ValidationResult:
    valid_rows: list[dict]
    error_rows: list[RowError]
    skipped_count: int = 0


def parse_float(value: str | None, field_name: str) -> tuple[float | None, str | None]:
    if value == "" or value is None:
        return None, None
    try:
        cleaned = (
            value.replace(",", "")
            .replace("$", "")
            .replace("£", "")
            .replace("€", "")
            .strip()
        )
        return float(cleaned), None
    except ValueError:
        return None, f"{field_name} must be a number, got '{value}'"


def parse_int(value: str | None, field_name: str) -> tuple[int | None, str | None]:
    if value == "" or value is None:
        return None, None
    try:
        cleaned = value.replace(",", "").strip()
        return int(float(cleaned)), None
    except ValueError:
        return None, f"{field_name} must be a whole number, got '{value}'"


def parse_date(value: str | None, field_name: str) -> tuple[str | None, str | None]:
    from datetime import datetime

    if value == "" or value is None:
        return None, None

    formats = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d"]
    for fmt in formats:
        try:
            return datetime.strptime(value.strip(), fmt).strftime("%Y-%m-%d"), None
        except ValueError:
            continue

    return None, f"{field_name} is not a valid date, got '{value}'. Use YYYY-MM-DD format."
