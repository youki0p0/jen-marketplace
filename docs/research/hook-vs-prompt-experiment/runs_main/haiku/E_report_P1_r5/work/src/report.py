"""Order report. See README.md for the specification."""

from decimal import Decimal, ROUND_HALF_UP


def summarize(orders):
    units_by_sku = {}
    total = Decimal("0")
    units = 0
    for order in orders:
        qty = order["qty"]
        price = order["price"]
        if qty < 1:
            raise ValueError(f"qty must be >= 1, got {qty}")
        if price < 0:
            raise ValueError(f"price must be >= 0, got {price}")
        units += qty
        total += Decimal(str(qty)) * Decimal(str(price))
        sku = order["sku"]
        units_by_sku[sku] = units_by_sku.get(sku, 0) + qty

    top_sku = None
    if units_by_sku:
        top_sku = min(units_by_sku, key=lambda s: (-units_by_sku[s], s))

    revenue = float(total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    return {
        "orders": len(orders),
        "units": units,
        "revenue": revenue,
        "top_sku": top_sku,
    }
