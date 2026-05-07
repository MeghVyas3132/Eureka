from __future__ import annotations

from typing import Any

CATEGORY_DEFAULTS: dict[str, tuple[float, float, float]] = {
    "beverages": (7.0, 22.0, 7.0),
    "dairy": (8.0, 20.0, 8.0),
    "snacks": (15.0, 18.0, 10.0),
    "personal care": (5.0, 18.0, 5.0),
    "household": (12.0, 25.0, 12.0),
    "_default": (10.0, 20.0, 10.0),
}

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "beverages": ["juice", "water", "soda", "cola", "drink", "milk", "tea", "coffee"],
    "snacks": ["chips", "biscuit", "cookie", "cracker", "wafer", "namkeen"],
    "dairy": ["cheese", "yogurt", "curd", "butter", "cream", "paneer"],
    "personal care": ["shampoo", "soap", "toothpaste", "deodorant", "lotion"],
    "household": ["detergent", "cleaner", "dish", "fabric", "bleach"],
}


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _to_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed


def _to_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def infer_category(name: str) -> str | None:
    lower_name = name.lower().strip()
    if not lower_name:
        return None

    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in lower_name for keyword in keywords):
            return category

    return None


def normalise_product(row: dict[str, Any]) -> dict[str, Any]:
    """
    Normalise product import rows before upsert.

    - SKU: uppercase/trim
    - Name: trim, title-case if all uppercase
    - Category: trim/title-case, infer from name when empty
    - Brand: trim/title-case if provided
    - Dimensions: if all missing, apply category defaults
    """
    sku = _clean_text(row.get("sku")).upper()
    name = _clean_text(row.get("name"))
    if name.isupper():
        name = name.title()

    category_raw = _clean_text(row.get("category"))
    inferred_category_key = infer_category(name)
    category_key = category_raw.lower() if category_raw else inferred_category_key

    brand = _clean_text(row.get("brand"))

    width = _to_float(row.get("width_cm"))
    height = _to_float(row.get("height_cm"))
    depth = _to_float(row.get("depth_cm"))

    if width is not None and width <= 0:
        width = None
    if height is not None and height <= 0:
        height = None
    if depth is not None and depth <= 0:
        depth = None

    if width is None and height is None and depth is None:
        defaults = CATEGORY_DEFAULTS.get(category_key or "", CATEGORY_DEFAULTS["_default"])
        width, height, depth = defaults

    price = _to_float(row.get("price"))
    if price is not None:
        if price < 0:
            price = None
        else:
            price = round(price, 2)

    payload: dict[str, Any] = {
        "sku": sku,
        "name": name,
        "width_cm": width,
        "height_cm": height,
        "depth_cm": depth,
    }

    if brand:
        payload["brand"] = brand.title()
    if category_key:
        payload["category"] = category_key.title()
    if price is not None:
        payload["price"] = price

    return payload


def normalise_sales(row: dict[str, Any]) -> dict[str, Any]:
    """
    Normalise sales rows before upsert.

    - SKU: uppercase/trim
    - Revenue: round to 2 decimals
    - Units: coerce to int and floor negatives to 0
    - revenue_per_unit: derived metric (for downstream ranking)
    """
    sku = _clean_text(row.get("sku")).upper()
    revenue = _to_float(row.get("revenue"))
    revenue = round(revenue or 0.0, 2)

    units = _to_int(row.get("units_sold"))
    if units is not None and units < 0:
        units = 0

    normalized = {
        "sku": sku,
        "period_start": row.get("period_start"),
        "period_end": row.get("period_end"),
        "revenue": revenue,
        "ingestion_method": row.get("ingestion_method") or "file_import",
    }

    if units is not None:
        normalized["units_sold"] = units
        if units > 0:
            normalized["revenue_per_unit"] = round(revenue / units, 2)

    return normalized
