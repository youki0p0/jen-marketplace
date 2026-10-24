"""Money helpers. See README.md for the specification."""
from decimal import Decimal, ROUND_HALF_UP

_CENT = Decimal("0.01")


def to_cents(amount):
    d = Decimal(str(amount))
    if d < 0:
        raise ValueError("amount must not be negative")
    return int((d * 100).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def apply_tax(amount, rate_pct):
    a = Decimal(str(amount))
    r = Decimal(str(rate_pct))
    if a < 0 or r < 0:
        raise ValueError("amount and rate_pct must not be negative")
    return float((a * (1 + r / 100)).quantize(_CENT, rounding=ROUND_HALF_UP))


def split_bill(total, n):
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        raise ValueError("n must be an int >= 1")
    t = Decimal(str(total))
    share = (t / n).quantize(_CENT, rounding=ROUND_HALF_UP)
    parts = [share] * (n - 1)
    parts.append(t - share * (n - 1))
    return [float(p) for p in parts]
