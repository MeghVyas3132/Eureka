from __future__ import annotations

import math
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from services.assortment_filter import AssortmentResult, filter_assortment

STORE_TYPE_RULES: dict[str, dict[str, Any]] = {
    "supermarket": {
        "max_skus": 150,
        "max_facings": 4,
        "prioritise_by": "revenue",
        "category_blocking": True,
        "eye_level_pct": 0.20,
        "low_level_categories": ["bulk", "household", "water", "oil"],
    },
    "convenience": {
        "max_skus": 50,
        "max_facings": 3,
        "prioritise_by": "units",
        "category_blocking": True,
        "eye_level_pct": 0.30,
        "low_level_categories": ["household", "cleaning"],
    },
    "hypermarket": {
        "max_skus": 300,
        "max_facings": 6,
        "prioritise_by": "revenue",
        "category_blocking": True,
        "eye_level_pct": 0.15,
        "low_level_categories": ["bulk", "water", "rice", "flour", "oil"],
    },
    "specialty": {
        "max_skus": 80,
        "max_facings": 5,
        "prioritise_by": "revenue",
        "category_blocking": False,
        "eye_level_pct": 0.25,
        "low_level_categories": [],
    },
    "wholesale": {
        "max_skus": 200,
        "max_facings": 2,
        "prioritise_by": "units",
        "category_blocking": True,
        "eye_level_pct": 0.20,
        "low_level_categories": [],
    },
    "_default": {
        "max_skus": 100,
        "max_facings": 3,
        "prioritise_by": "revenue",
        "category_blocking": True,
        "eye_level_pct": 0.20,
        "low_level_categories": [],
    },
}

CATEGORY_COLORS = {
    "dairy": "#4A90D9",
    "beverages": "#7ED321",
    "snacks": "#F5A623",
    "personal care": "#9B59B6",
    "household": "#E74C3C",
    "bakery": "#E67E22",
    "frozen": "#1ABC9C",
    "_default": "#95A5A6",
}


@dataclass
class PlanogramInput:
    store_id: uuid.UUID
    store: Any
    generation_level: str
    products: list[Any]
    sales: list[Any]
    shelf_count: int = 5
    shelf_width_cm: float = 180.0
    shelf_height_cm: float = 200.0


@dataclass
class RankedSKU:
    product: Any
    sales_score: float
    category_rank: int
    overall_rank: int
    suggested_facings: int
    placement_tier: str
    revenue: float
    units_sold: int


@dataclass
class ShelfAssignment:
    shelf_number: int
    product_id: uuid.UUID
    sku: str
    position_x_cm: float
    facing_count: int
    placement_tier: str


@dataclass
class ConfidenceScore:
    score: float
    tier: str
    sales_coverage_pct: float
    dimension_coverage_pct: float
    category_coverage_pct: float
    store_parse_confidence: float


@dataclass
class DataQualityWarning:
    code: str
    severity: str
    message: str
    action_label: str
    action_url: str


@dataclass
class PlanogramGenerationResult:
    planogram_json: dict[str, Any]
    assortment: AssortmentResult
    confidence: ConfidenceScore
    warnings: list[DataQualityWarning]


def get_product_color(category: str | None) -> str:
    key = (category or "_default").strip().lower()
    return CATEGORY_COLORS.get(key, CATEGORY_COLORS["_default"])


def _store_rules(store_type: str | None) -> dict[str, Any]:
    if store_type and store_type in STORE_TYPE_RULES:
        return STORE_TYPE_RULES[store_type]
    return STORE_TYPE_RULES["_default"]


def _safe_name(product: Any) -> str:
    return str(getattr(product, "name", "") or "")


def _safe_category(product: Any) -> str:
    return str(getattr(product, "category", "") or "Unknown")


def _safe_sku(product: Any) -> str:
    return str(getattr(product, "sku", "") or "").strip().upper()


def _safe_width(product: Any) -> float:
    width = getattr(product, "width_cm", None)
    if width is None or width <= 0:
        return 10.0
    return float(width)


def calculate_facings(product: Any, sales_score: float, shelf_width_cm: float, store_type: str) -> int:
    if sales_score > 0.7:
        base = 3
    elif sales_score > 0.4:
        base = 2
    else:
        base = 1

    width = _safe_width(product)
    capacity_cap = max(1, int(shelf_width_cm // width))
    store_cap = int(_store_rules(store_type).get("max_facings", 3))
    return max(1, min(base, capacity_cap, store_cap))


def rank_skus(
    products: list[Any],
    sales: list[Any],
    store_type: str,
    shelf_width_cm: float = 180.0,
) -> list[RankedSKU]:
    rules = _store_rules(store_type)

    sales_agg: dict[str, dict[str, float]] = {}
    for sale in sales:
        sku = str(getattr(sale, "sku", "") or "").strip().upper()
        if not sku:
            continue
        revenue = float(getattr(sale, "revenue", 0) or 0)
        units = int(getattr(sale, "units_sold", 0) or 0)
        if sku not in sales_agg:
            sales_agg[sku] = {"revenue": 0.0, "units": 0.0}
        sales_agg[sku]["revenue"] += revenue
        sales_agg[sku]["units"] += units

    max_revenue = max((data["revenue"] for data in sales_agg.values()), default=0.0)
    max_units = max((data["units"] for data in sales_agg.values()), default=0.0)

    category_totals: dict[str, float] = {}
    for product in products:
        sku = _safe_sku(product)
        category = _safe_category(product)
        category_totals.setdefault(category, 0.0)
        category_totals[category] += sales_agg.get(sku, {}).get("revenue", 0.0)

    if sales_agg:
        ordered_categories = sorted(category_totals.items(), key=lambda item: (-item[1], item[0].lower()))
    else:
        ordered_categories = sorted(category_totals.items(), key=lambda item: item[0].lower())

    category_rank_map = {category: idx + 1 for idx, (category, _) in enumerate(ordered_categories)}

    scored_products: list[tuple[Any, float, float, int, int]] = []
    for product in products:
        sku = _safe_sku(product)
        category = _safe_category(product)
        revenue = float(sales_agg.get(sku, {}).get("revenue", 0.0))
        units = int(sales_agg.get(sku, {}).get("units", 0.0))

        if max_revenue <= 0 and max_units <= 0:
            sales_score = 0.0
        else:
            revenue_component = revenue / max_revenue if max_revenue > 0 else 0.0
            units_component = units / max_units if max_units > 0 else 0.0
            if rules.get("prioritise_by") == "units":
                sales_score = (units_component * 0.7) + (revenue_component * 0.3)
            else:
                sales_score = (revenue_component * 0.7) + (units_component * 0.3)

        scored_products.append(
            (
                product,
                round(sales_score, 4),
                revenue,
                units,
                category_rank_map.get(category, 999),
            )
        )

    scored_products.sort(
        key=lambda item: (
            item[4],
            -item[1],
            _safe_name(item[0]).lower(),
        )
    )

    low_level_keywords = [value.lower() for value in rules.get("low_level_categories", [])]
    eye_level_pct = float(rules.get("eye_level_pct", 0.2))

    ranked: list[RankedSKU] = []
    eye_level_count = max(1, math.ceil(len(scored_products) * eye_level_pct)) if scored_products else 0

    for idx, (product, score, revenue, units, category_rank) in enumerate(scored_products, start=1):
        category = _safe_category(product).lower()
        forced_low = any(keyword in category for keyword in low_level_keywords)

        if forced_low:
            placement_tier = "low_level"
        elif idx <= eye_level_count:
            placement_tier = "eye_level"
        elif idx <= max(eye_level_count + 1, math.ceil(len(scored_products) * 0.7)):
            placement_tier = "mid_level"
        else:
            placement_tier = "top_level"

        ranked.append(
            RankedSKU(
                product=product,
                sales_score=score,
                category_rank=category_rank,
                overall_rank=idx,
                suggested_facings=calculate_facings(product, score, shelf_width_cm, store_type),
                placement_tier=placement_tier,
                revenue=round(revenue, 2),
                units_sold=units,
            )
        )

    return ranked


def _tier_shelves(shelf_count: int) -> dict[str, list[int]]:
    if shelf_count <= 1:
        return {
            "top_level": [1],
            "eye_level": [1],
            "mid_level": [1],
            "low_level": [1],
        }

    eye_shelf = min(2, shelf_count)
    low_shelf = shelf_count
    top_shelf = 1
    mid_shelves = [number for number in range(1, shelf_count + 1) if number not in {top_shelf, eye_shelf, low_shelf}]

    if not mid_shelves:
        mid_shelves = [eye_shelf]

    return {
        "top_level": [top_shelf],
        "eye_level": [eye_shelf],
        "mid_level": mid_shelves,
        "low_level": [low_shelf],
    }


def assign_to_shelves(
    ranked_skus: list[RankedSKU],
    shelf_count: int,
    shelf_width_cm: float,
    store_type: str,
) -> tuple[list[ShelfAssignment], list[str], dict[int, float]]:
    if shelf_count <= 0:
        shelf_count = 1

    rules = _store_rules(store_type)
    tiers = _tier_shelves(shelf_count)

    shelf_remaining = {shelf: shelf_width_cm for shelf in range(1, shelf_count + 1)}
    shelf_position = {shelf: 0.0 for shelf in range(1, shelf_count + 1)}

    assignments: list[ShelfAssignment] = []
    overflow_skus: list[str] = []

    for ranked in ranked_skus:
        ranked.suggested_facings = calculate_facings(
            ranked.product,
            ranked.sales_score,
            shelf_width_cm,
            store_type,
        )

        preferred = list(tiers.get(ranked.placement_tier, tiers["mid_level"]))
        fallback = [s for s in range(1, shelf_count + 1) if s not in preferred]
        candidate_shelves = preferred + fallback

        width = _safe_width(ranked.product)
        max_facings = int(rules.get("max_facings", 3))
        facings = min(ranked.suggested_facings, max_facings)

        placed = False
        for shelf_number in candidate_shelves:
            while facings >= 1:
                required = width * facings
                if required <= shelf_remaining[shelf_number]:
                    assignments.append(
                        ShelfAssignment(
                            shelf_number=shelf_number,
                            product_id=getattr(ranked.product, "id"),
                            sku=_safe_sku(ranked.product),
                            position_x_cm=round(shelf_position[shelf_number], 2),
                            facing_count=facings,
                            placement_tier=ranked.placement_tier,
                        )
                    )
                    shelf_position[shelf_number] += required
                    shelf_remaining[shelf_number] -= required
                    placed = True
                    break
                facings -= 1
            if placed:
                break
            facings = min(ranked.suggested_facings, max_facings)

        if not placed:
            overflow_skus.append(_safe_sku(ranked.product))
            last_shelf = shelf_count
            required = width
            assignments.append(
                ShelfAssignment(
                    shelf_number=last_shelf,
                    product_id=getattr(ranked.product, "id"),
                    sku=_safe_sku(ranked.product),
                    position_x_cm=round(shelf_position[last_shelf], 2),
                    facing_count=1,
                    placement_tier=ranked.placement_tier,
                )
            )
            shelf_position[last_shelf] += required
            shelf_remaining[last_shelf] -= required

    return assignments, overflow_skus, shelf_remaining


def compute_confidence_score(
    products: list[Any],
    sales: list[Any],
    store_parse_confidence: float,
    assortment: AssortmentResult,
) -> ConfidenceScore:
    included_skus = set(assortment.included_skus)
    if not included_skus:
        included_skus = {str(getattr(product, "sku", "") or "").strip().upper() for product in products}

    included_skus.discard("")
    total = max(1, len(included_skus))

    sales_skus = {
        str(getattr(row, "sku", "") or "").strip().upper()
        for row in sales
        if float(getattr(row, "revenue", 0) or 0) > 0
    }
    sales_coverage_pct = (len(included_skus.intersection(sales_skus)) / total) * 100.0

    products_by_sku = {
        _safe_sku(product): product
        for product in products
        if _safe_sku(product)
    }

    dimensions_count = 0
    category_count = 0
    for sku in included_skus:
        product = products_by_sku.get(sku)
        if not product:
            continue
        if getattr(product, "width_cm", None) and getattr(product, "height_cm", None):
            dimensions_count += 1
        if str(getattr(product, "category", "") or "").strip():
            category_count += 1

    dimension_coverage_pct = (dimensions_count / total) * 100.0
    category_coverage_pct = (category_count / total) * 100.0

    store_conf = max(0.0, min(1.0, float(store_parse_confidence or 0.0)))

    score = (
        (sales_coverage_pct / 100.0) * 0.40
        + (dimension_coverage_pct / 100.0) * 0.30
        + (category_coverage_pct / 100.0) * 0.15
        + (store_conf * 0.15)
    )

    if score >= 0.75:
        tier = "high"
    elif score >= 0.45:
        tier = "medium"
    else:
        tier = "low"

    return ConfidenceScore(
        score=round(score, 2),
        tier=tier,
        sales_coverage_pct=round(sales_coverage_pct, 1),
        dimension_coverage_pct=round(dimension_coverage_pct, 1),
        category_coverage_pct=round(category_coverage_pct, 1),
        store_parse_confidence=round(store_conf, 2),
    )


def build_data_quality_warnings(
    confidence: ConfidenceScore,
    assortment: AssortmentResult,
    store: Any,
) -> list[DataQualityWarning]:
    warnings: list[DataQualityWarning] = []
    store_id = getattr(store, "id", "")

    if confidence.sales_coverage_pct < 50:
        warnings.append(
            DataQualityWarning(
                code="low_sales_coverage",
                severity="high",
                message="Sales coverage is below 50%. Ranking quality is likely impacted.",
                action_label="Upload store sales data",
                action_url=f"/stores/{store_id}/data?tab=import",
            )
        )

    if confidence.dimension_coverage_pct < 40:
        warnings.append(
            DataQualityWarning(
                code="low_dimension_coverage",
                severity="medium",
                message="Many products are missing dimensions. Default sizes were used.",
                action_label="Add product dimensions",
                action_url="/products?filter=missing_dimensions",
            )
        )

    if confidence.category_coverage_pct < 60:
        warnings.append(
            DataQualityWarning(
                code="low_category_coverage",
                severity="medium",
                message="Category metadata is incomplete, reducing layout quality.",
                action_label="Add product categories",
                action_url="/products?filter=missing_category",
            )
        )

    if confidence.store_parse_confidence < 0.5:
        warnings.append(
            DataQualityWarning(
                code="store_location_uncertain",
                severity="low",
                message="Store location parsing confidence is low. Review store details.",
                action_label="Review store details",
                action_url=f"/stores/{store_id}/edit",
            )
        )

    if assortment.filter_method == "top_n":
        warnings.append(
            DataQualityWarning(
                code="no_sales_assortment",
                severity="high",
                message="No sales data found. Assortment was estimated using fallback ranking.",
                action_label="Import sales data",
                action_url=f"/stores/{store_id}/data?tab=import",
            )
        )

    severity_rank = {"high": 0, "medium": 1, "low": 2}
    warnings.sort(key=lambda warning: severity_rank.get(warning.severity, 3))
    return warnings


def _build_planogram_json(
    *,
    input_data: PlanogramInput,
    assortment: AssortmentResult,
    ranked: list[RankedSKU],
    assignments: list[ShelfAssignment],
    overflow_skus: list[str],
    shelf_remaining: dict[int, float],
    confidence: ConfidenceScore,
    warnings: list[DataQualityWarning],
) -> dict[str, Any]:
    ranked_by_sku = {_safe_sku(ranked_row.product): ranked_row for ranked_row in ranked}
    product_by_sku = {_safe_sku(ranked_row.product): ranked_row.product for ranked_row in ranked}

    shelves: dict[int, dict[str, Any]] = {
        shelf_number: {
            "shelf_number": shelf_number,
            "tier": "mid_level",
            "remaining_width_cm": round(max(0.0, shelf_remaining.get(shelf_number, 0.0)), 2),
            "products": [],
        }
        for shelf_number in range(1, input_data.shelf_count + 1)
    }

    tier_map = _tier_shelves(input_data.shelf_count)
    for tier_name, tier_shelves in tier_map.items():
        for shelf_number in tier_shelves:
            if shelf_number in shelves:
                shelves[shelf_number]["tier"] = tier_name

    category_summary: dict[str, dict[str, Any]] = {}

    for assignment in assignments:
        sku = assignment.sku
        product = product_by_sku.get(sku)
        ranked_row = ranked_by_sku.get(sku)
        if not product or not ranked_row:
            continue

        width = _safe_width(product)
        total_width = width * assignment.facing_count
        category = _safe_category(product)

        shelves[assignment.shelf_number]["products"].append(
            {
                "product_id": str(getattr(product, "id")),
                "sku": sku,
                "name": _safe_name(product),
                "brand": getattr(product, "brand", None),
                "category": category,
                "position_x_cm": round(assignment.position_x_cm, 2),
                "width_cm": round(width, 2),
                "height_cm": round(float(getattr(product, "height_cm", 20.0) or 20.0), 2),
                "facing_count": assignment.facing_count,
                "total_width_cm": round(total_width, 2),
                "sales_score": ranked_row.sales_score,
                "revenue": ranked_row.revenue,
                "units_sold": ranked_row.units_sold,
                "placement_tier": assignment.placement_tier,
                "color_hex": get_product_color(category),
            }
        )

        if category not in category_summary:
            category_summary[category] = {
                "sku_count": 0,
                "total_revenue": 0.0,
                "shelves": set(),
            }
        category_summary[category]["sku_count"] += 1
        category_summary[category]["total_revenue"] += ranked_row.revenue
        category_summary[category]["shelves"].add(assignment.shelf_number)

    category_summary_json = {
        category: {
            "sku_count": values["sku_count"],
            "total_revenue": round(values["total_revenue"], 2),
            "shelves": sorted(values["shelves"]),
        }
        for category, values in category_summary.items()
    }

    return {
        "planogram_id": None,
        "store_id": str(input_data.store_id),
        "generation_level": input_data.generation_level,
        "generation_method": "auto",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "has_sales_data": bool(input_data.sales),
        "confidence": {
            "score": confidence.score,
            "tier": confidence.tier,
            "sales_coverage_pct": confidence.sales_coverage_pct,
            "dimension_coverage_pct": confidence.dimension_coverage_pct,
            "category_coverage_pct": confidence.category_coverage_pct,
            "store_parse_confidence": confidence.store_parse_confidence,
        },
        "assortment": {
            "total_catalogue_skus": len(input_data.products),
            "included_skus": len(assortment.included_skus),
            "excluded_skus": len(assortment.excluded_skus),
            "filter_method": assortment.filter_method,
            "coverage_pct": assortment.coverage_pct,
            "message": assortment.message,
        },
        "data_quality_warnings": [
            {
                "code": warning.code,
                "severity": warning.severity,
                "message": warning.message,
                "action_label": warning.action_label,
                "action_url": warning.action_url,
            }
            for warning in warnings
        ],
        "shelf_config": {
            "shelf_count": input_data.shelf_count,
            "shelf_width_cm": input_data.shelf_width_cm,
            "shelf_height_cm": input_data.shelf_height_cm,
            "shelf_depth_cm": 40.0,
            "shelf_spacing_cm": round(input_data.shelf_height_cm / max(input_data.shelf_count, 1), 2),
            "store_type": str(getattr(input_data.store, "store_type", "unknown") or "unknown"),
            "store_type_rules_applied": True,
        },
        "shelves": [shelves[shelf_number] for shelf_number in sorted(shelves.keys())],
        "overflow_skus": overflow_skus,
        "category_summary": category_summary_json,
    }


def generate(input_data: PlanogramInput) -> PlanogramGenerationResult:
    store_type = str(getattr(input_data.store, "store_type", "unknown") or "unknown")

    assortment = filter_assortment(
        products=input_data.products,
        sales=input_data.sales,
        store_type=store_type,
        shelf_count=input_data.shelf_count,
        shelf_width_cm=input_data.shelf_width_cm,
    )

    included_skus = set(assortment.included_skus)
    filtered_products = [product for product in input_data.products if _safe_sku(product) in included_skus]

    ranked = rank_skus(
        filtered_products,
        input_data.sales,
        store_type,
        shelf_width_cm=input_data.shelf_width_cm,
    )
    assignments, overflow_skus, shelf_remaining = assign_to_shelves(
        ranked_skus=ranked,
        shelf_count=input_data.shelf_count,
        shelf_width_cm=input_data.shelf_width_cm,
        store_type=store_type,
    )

    confidence = compute_confidence_score(
        filtered_products,
        input_data.sales,
        float(getattr(input_data.store, "parse_confidence", 0.0) or 0.0),
        assortment,
    )
    warnings = build_data_quality_warnings(confidence, assortment, input_data.store)

    planogram_json = _build_planogram_json(
        input_data=input_data,
        assortment=assortment,
        ranked=ranked,
        assignments=assignments,
        overflow_skus=overflow_skus,
        shelf_remaining=shelf_remaining,
        confidence=confidence,
        warnings=warnings,
    )

    return PlanogramGenerationResult(
        planogram_json=planogram_json,
        assortment=assortment,
        confidence=confidence,
        warnings=warnings,
    )
