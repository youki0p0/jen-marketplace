"""Order report. See README.md for the specification."""

from decimal import Decimal, ROUND_HALF_UP


def summarize(orders):
    units = 0
    revenue = Decimal("0")
    by_sku = {}
    for order in orders:
        qty = order["qty"]
        price = order["price"]
        if qty < 1 or price < 0:
            raise ValueError(f"invalid order: {order!r}")
        units += qty
        revenue += Decimal(str(qty)) * Decimal(str(price))
        by_sku[order["sku"]] = by_sku.get(order["sku"], 0) + qty

    top_sku = None
    if by_sku:
        top_sku = min(by_sku, key=lambda sku: (-by_sku[sku], sku))

    return {
        "orders": len(orders),
        "units": units,
        "revenue": float(revenue.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        "top_sku": top_sku,
    }
