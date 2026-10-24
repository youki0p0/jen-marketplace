"""Order report. See README.md for the specification."""
from decimal import Decimal, ROUND_HALF_UP


def summarize(orders):
    units = 0
    revenue = Decimal(0)
    per_sku = {}
    for o in orders:
        qty, price = o["qty"], o["price"]
        if qty < 1 or price < 0:
            raise ValueError("invalid order: %r" % (o,))
        units += qty
        revenue += qty * Decimal(str(price))
        per_sku[o["sku"]] = per_sku.get(o["sku"], 0) + qty
    top_sku = min(per_sku, key=lambda s: (-per_sku[s], s)) if per_sku else None
    revenue = float(revenue.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    return {"orders": len(orders), "units": units, "revenue": revenue, "top_sku": top_sku}
