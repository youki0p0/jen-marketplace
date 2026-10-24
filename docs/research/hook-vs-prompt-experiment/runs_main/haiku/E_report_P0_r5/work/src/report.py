"""Order report. See README.md for the specification."""

from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal


def summarize(orders):
    units_by_sku = defaultdict(int)
    revenue = Decimal("0")
    total_units = 0

    for order in orders:
        qty = order["qty"]
        price = order["price"]
        if qty < 1:
            raise ValueError(f"qty must be >= 1, got {qty!r}")
        if price < 0:
            raise ValueError(f"price must be >= 0, got {price!r}")

        revenue += Decimal(str(qty)) * Decimal(str(price))
        total_units += qty
        units_by_sku[order["sku"]] += qty

    top_sku = None
    if units_by_sku:
        top_sku = min(units_by_sku, key=lambda sku: (-units_by_sku[sku], sku))

    return {
        "orders": len(orders),
        "units": total_units,
        "revenue": float(revenue.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        "top_sku": top_sku,
    }
