"""Order report. See README.md for the specification."""
from decimal import Decimal, ROUND_HALF_UP


def summarize(orders):
    units = 0
    total = Decimal(0)
    by_sku = {}
    for o in orders:
        if o["qty"] < 1 or o["price"] < 0:
            raise ValueError("invalid order: %r" % (o,))
        units += o["qty"]
        total += Decimal(str(o["qty"])) * Decimal(str(o["price"]))
        by_sku[o["sku"]] = by_sku.get(o["sku"], 0) + o["qty"]
    top = min(by_sku, key=lambda s: (-by_sku[s], s)) if by_sku else None
    revenue = float(total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    return {"orders": len(orders), "units": units, "revenue": revenue, "top_sku": top}
