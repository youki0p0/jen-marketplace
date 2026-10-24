"""Order report. See README.md for the specification."""

from decimal import ROUND_HALF_UP, Decimal


def summarize(orders):
    units_by_sku = {}
    total_units = 0
    revenue = Decimal("0")
    for order in orders:
        qty = order["qty"]
        price = order["price"]
        if qty < 1 or price < 0:
            raise ValueError(f"invalid order: {order!r}")
        total_units += qty
        revenue += Decimal(str(qty)) * Decimal(str(price))
        units_by_sku[order["sku"]] = units_by_sku.get(order["sku"], 0) + qty

    top_sku = None
    if units_by_sku:
        top_sku = min(units_by_sku, key=lambda sku: (-units_by_sku[sku], sku))

    return {
        "orders": len(orders),
        "units": total_units,
        "revenue": float(revenue.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        "top_sku": top_sku,
    }
