from decimal import Decimal, ROUND_HALF_UP
def summarize(orders):
    units, rev, by = 0, Decimal(0), {}
    for o in orders:
        if o["qty"] < 1 or o["price"] < 0: raise ValueError
        units += o["qty"]; rev += Decimal(str(o["qty"])) * Decimal(str(o["price"]))
        by[o["sku"]] = by.get(o["sku"], 0) + o["qty"]
    top = min(by, key=lambda s: (-by[s], s)) if by else None
    return {"orders": len(orders), "units": units,
            "revenue": float(rev.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)), "top_sku": top}
