"""Order report. See README.md for the specification."""

from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal


def summarize(orders):
    units_by_sku = defaultdict(int)
    total = Decimal("0")
    units = 0

    for order in orders:
        qty = order["qty"]
        price = order["price"]
        if qty < 1 or price < 0:
            raise ValueError(f"invalid order: {order!r}")
        units += qty
        units_by_sku[order["sku"]] += qty
        total += Decimal(str(qty)) * Decimal(str(price))

    top_sku = None
    if units_by_sku:
        top_sku = min(units_by_sku, key=lambda sku: (-units_by_sku[sku], sku))

    revenue = total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return {
        "orders": len(orders),
        "units": units,
        "revenue": float(revenue),
        "top_sku": top_sku,
    }
