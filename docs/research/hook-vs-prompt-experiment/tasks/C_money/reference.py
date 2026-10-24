from decimal import Decimal, ROUND_HALF_UP
Q = Decimal("0.01")
def _d(x): return Decimal(str(x))
def to_cents(amount):
    a = _d(amount)
    if a < 0: raise ValueError
    return int((a * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
def apply_tax(amount, rate_pct):
    a, r = _d(amount), _d(rate_pct)
    if a < 0 or r < 0: raise ValueError
    return float((a * (1 + r / 100)).quantize(Q, rounding=ROUND_HALF_UP))
def split_bill(total, n):
    if not isinstance(n, int) or isinstance(n, bool) or n < 1: raise ValueError
    t = _d(total)
    part = (t / n).quantize(Q, rounding=ROUND_HALF_UP)
    return [float(part)] * (n - 1) + [float(t - part * (n - 1))]
