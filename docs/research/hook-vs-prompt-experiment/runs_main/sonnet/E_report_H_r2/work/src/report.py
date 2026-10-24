"""Order report. See README.md for the specification."""
from decimal import Decimal, ROUND_HALF_UP


def summarize(orders):
    units = 0
    revenue = Decimal(0)
    by_sku = {}
    for o in orders:
        if o["qty"] < 1 or o["price"] < 0:
            raise ValueError("invalid order: %r" % (o,))
        units += o["qty"]
        revenue += o["qty"] * Decimal(str(o["price"]))
        by_sku[o["sku"]] = by_sku.get(o["sku"], 0) + o["qty"]
    top = min(by_sku, key=lambda s: (-by_sku[s], s)) if by_sku else None
    return {
        "orders": len(orders),
        "units": units,
        "revenue": float(revenue.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        "top_sku": top,
    }
