"""Order report. See README.md for the specification."""
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP


def summarize(orders):
    units = 0
    total = Decimal(0)
    per_sku = defaultdict(int)
    for o in orders:
        if o["qty"] < 1 or o["price"] < 0:
            raise ValueError("invalid order: %r" % (o,))
        units += o["qty"]
        total += o["qty"] * Decimal(str(o["price"]))
        per_sku[o["sku"]] += o["qty"]
    top = min(per_sku, key=lambda s: (-per_sku[s], s)) if per_sku else None
    revenue = float(total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    return {"orders": len(orders), "units": units, "revenue": revenue, "top_sku": top}
