from __future__ import annotations

from dataclasses import dataclass
from math import floor
from typing import Any

STORE_TYPE_SKU_LIMITS = {
    "supermarket": 150,
    "hypermarket": 300,
    "convenience": 50,
    "specialty": 80,
    "wholesale": 200,
    "unknown": 100,
}


@dataclass
class AssortmentResult:
    included_skus: list[str]
    excluded_skus: list[str]
    filter_method: str
    coverage_pct: float
    message: str


def _alphabetical_catalogue(products: list[Any]) -> list[Any]:
    return sorted(
        products,
        key=lambda p: (
            str(getattr(p, "category", "") or "").lower(),
            str(getattr(p, "name", "") or "").lower(),
            str(getattr(p, "sku", "") or "").upper(),
        ),
    )


def _price_ranked_catalogue(products: list[Any]) -> list[Any]:
    with_price = [p for p in products if getattr(p, "price", None) is not None]
    without_price = [p for p in products if getattr(p, "price", None) is None]

    with_price_sorted = sorted(
        with_price,
        key=lambda p: (-(getattr(p, "price", 0) or 0), str(getattr(p, "name", "") or "").lower()),
    )
    without_price_sorted = _alphabetical_catalogue(without_price)

    return with_price_sorted + without_price_sorted


def filter_assortment(
    products: list[Any],
    sales: list[Any],
    store_type: str,
    shelf_count: int,
    shelf_width_cm: float,
) -> AssortmentResult:
    if not products:
        return AssortmentResult(
            included_skus=[],
            excluded_skus=[],
            filter_method="all",
            coverage_pct=0.0,
            message="No products found in catalogue.",
        )

    products_by_sku: dict[str, Any] = {}
    for product in products:
        sku = str(getattr(product, "sku", "") or "").strip().upper()
        if sku and sku not in products_by_sku:
            products_by_sku[sku] = product

    catalogue_skus = list(products_by_sku.keys())
    total_catalogue = len(catalogue_skus)

    if total_catalogue == 0:
        return AssortmentResult(
            included_skus=[],
            excluded_skus=[],
            filter_method="all",
            coverage_pct=0.0,
            message="No valid product SKUs found in catalogue.",
        )

    store_limit = STORE_TYPE_SKU_LIMITS.get(store_type, STORE_TYPE_SKU_LIMITS["unknown"])
    max_skus_by_shelf = max(1, floor((shelf_count * shelf_width_cm) / 10.0))
    hard_limit = max(1, min(store_limit, max_skus_by_shelf))

    sales_aggregate: dict[str, tuple[float, int]] = {}
    for sale in sales:
        sku = str(getattr(sale, "sku", "") or "").strip().upper()
        if sku not in products_by_sku:
            continue

        revenue = float(getattr(sale, "revenue", 0) or 0)
        units = int(getattr(sale, "units_sold", 0) or 0)
        prev_revenue, prev_units = sales_aggregate.get(sku, (0.0, 0))
        sales_aggregate[sku] = (prev_revenue + revenue, prev_units + units)

    sales_skus_ranked = sorted(
        sales_aggregate.keys(),
        key=lambda sku: (
            -sales_aggregate[sku][0],
            -sales_aggregate[sku][1],
            str(getattr(products_by_sku[sku], "name", "") or "").lower(),
        ),
    )

    sales_coverage_pct = (len(sales_skus_ranked) / total_catalogue) * 100.0

    included: list[str]
    method: str
    message: str

    if sales_skus_ranked and sales_coverage_pct >= 20.0:
        included = sales_skus_ranked[:hard_limit]
        method = "sales_coverage"
        message = (
            f"Showing {len(included)} SKUs with sales data. "
            f"{max(0, total_catalogue - len(included))} catalogue products excluded."
        )
    elif sales_skus_ranked:
        included = list(sales_skus_ranked)
        fill_candidates = [
            p
            for p in _alphabetical_catalogue(list(products_by_sku.values()))
            if str(getattr(p, "sku", "") or "").strip().upper() not in set(included)
        ]
        for product in fill_candidates:
            if len(included) >= hard_limit:
                break
            included.append(str(getattr(product, "sku", "") or "").strip().upper())

        method = "sales_coverage"
        missing_pct = round(100.0 - sales_coverage_pct, 1)
        message = (
            f"{missing_pct}% of your products have no sales data - "
            "remainder filled alphabetically."
        )
    else:
        ranked = _price_ranked_catalogue(list(products_by_sku.values()))
        included = [str(getattr(p, "sku", "") or "").strip().upper() for p in ranked[:hard_limit]]
        method = "top_n"
        message = "No sales data available. Selected top SKUs by price and alphabetical fallback."

    if not included:
        included = catalogue_skus[:hard_limit]
        method = "all"
        message = "Fallback applied: returning catalogue SKUs because filters produced zero rows."

    if len(included) > hard_limit:
        included = included[:hard_limit]

    included_set = set(included)
    excluded = [sku for sku in catalogue_skus if sku not in included_set]

    coverage_pct = round((len(included) / total_catalogue) * 100.0, 1)

    return AssortmentResult(
        included_skus=included,
        excluded_skus=excluded,
        filter_method=method,
        coverage_pct=coverage_pct,
        message=message,
    )
