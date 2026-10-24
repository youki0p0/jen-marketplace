from decimal import Decimal, ROUND_HALF_UP
Q = Decimal("0.01")
def line_total(unit_price, qty, discount_pct=0.0):
    if not isinstance(qty, int) or isinstance(qty, bool) or qty < 1: raise ValueError
    if not (0 <= discount_pct <= 100): raise ValueError
    if unit_price < 0: raise ValueError
    v = Decimal(str(unit_price)) * qty * (1 - Decimal(str(discount_pct)) / 100)
    return float(v.quantize(Q, rounding=ROUND_HALF_UP))
def invoice_total(lines):
    s = sum((Decimal(str(line_total(*l))) for l in lines), Decimal(0))
    return float(s.quantize(Q, rounding=ROUND_HALF_UP))
