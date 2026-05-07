from types import SimpleNamespace

from services.assortment_filter import filter_assortment


def _product(sku: str, category: str = "Dairy", price: float | None = None):
    return SimpleNamespace(sku=sku, name=f"Product {sku}", category=category, price=price)


def _sale(sku: str, revenue: float, units: int):
    return SimpleNamespace(sku=sku, revenue=revenue, units_sold=units)


def test_filter_uses_sales_coverage_when_coverage_is_sufficient():
    products = [_product(f"SKU-{idx:03d}") for idx in range(1, 11)]
    sales = [_sale("SKU-001", 1000, 20), _sale("SKU-002", 500, 10)]

    result = filter_assortment(
        products=products,
        sales=sales,
        store_type="convenience",
        shelf_count=5,
        shelf_width_cm=180,
    )

    assert result.filter_method == "sales_coverage"
    assert result.included_skus[:2] == ["SKU-001", "SKU-002"]


def test_filter_falls_back_to_top_n_when_no_sales_data():
    products = [
        _product("SKU-A", price=5.0),
        _product("SKU-B", price=10.0),
        _product("SKU-C", price=2.0),
    ]

    result = filter_assortment(
        products=products,
        sales=[],
        store_type="convenience",
        shelf_count=1,
        shelf_width_cm=30,
    )

    assert result.filter_method == "top_n"
    assert result.included_skus[0] == "SKU-B"
    assert len(result.included_skus) >= 1
