"""Order report. See README.md for the specification."""

from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP


def summarize(orders):
    units_by_sku = defaultdict(int)
    revenue = Decimal("0")
    total_units = 0

    for order in orders:
        qty = order["qty"]
        price = order["price"]
        if qty < 1:
            raise ValueError(f"qty must be >= 1, got {qty}")
        if price < 0:
            raise ValueError(f"price must be >= 0, got {price}")

        units_by_sku[order["sku"]] += qty
        total_units += qty
        revenue += Decimal(str(qty)) * Decimal(str(price))

    if not units_by_sku:
        top_sku = None
    else:
        top_sku = min(units_by_sku, key=lambda sku: (-units_by_sku[sku], sku))

    return {
        "orders": len(orders),
        "units": total_units,
        "revenue": float(revenue.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        "top_sku": top_sku,
    }
