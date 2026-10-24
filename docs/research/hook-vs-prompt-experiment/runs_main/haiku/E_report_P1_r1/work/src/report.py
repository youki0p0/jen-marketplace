"""Order report. See README.md for the specification."""

from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal


def summarize(orders):
    if not orders:
        return {"orders": 0, "units": 0, "revenue": 0.0, "top_sku": None}

    units = 0
    revenue = Decimal("0")
    by_sku = defaultdict(int)
    for order in orders:
        qty = order["qty"]
        price = order["price"]
        if qty < 1 or price < 0:
            raise ValueError(f"invalid order: {order!r}")
        units += qty
        revenue += Decimal(str(qty)) * Decimal(str(price))
        by_sku[order["sku"]] += qty

    # most units wins; ties go to the alphabetically first sku
    top_sku = min(by_sku, key=lambda sku: (-by_sku[sku], sku))

    return {
        "orders": len(orders),
        "units": units,
        "revenue": float(revenue.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        "top_sku": top_sku,
    }
