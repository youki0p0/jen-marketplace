"""Order report. See README.md for the specification."""
from decimal import Decimal, ROUND_HALF_UP


def summarize(orders):
    units = 0
    revenue = Decimal(0)
    per_sku = {}
    for o in orders:
        if o["qty"] < 1 or o["price"] < 0:
            raise ValueError("invalid order: %r" % (o,))
        units += o["qty"]
        revenue += o["qty"] * Decimal(str(o["price"]))
        per_sku[o["sku"]] = per_sku.get(o["sku"], 0) + o["qty"]
    top_sku = min(per_sku, key=lambda s: (-per_sku[s], s)) if per_sku else None
    revenue = float(revenue.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    return {"orders": len(orders), "units": units, "revenue": revenue, "top_sku": top_sku}
