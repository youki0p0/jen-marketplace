"""Money helpers. See README.md for the specification."""

from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("0.01")


def _dec(x):
    return Decimal(str(x))


def to_cents(amount):
    value = _dec(amount)
    if value < 0:
        raise ValueError("amount must not be negative")
    return int((value * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def apply_tax(amount, rate_pct):
    value = _dec(amount)
    rate = _dec(rate_pct)
    if value < 0 or rate < 0:
        raise ValueError("amount and rate_pct must not be negative")
    total = value * (1 + rate / 100)
    return float(total.quantize(CENT, rounding=ROUND_HALF_UP))


def split_bill(total, n):
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        raise ValueError("n must be an int >= 1")
    total = _dec(total)
    share = (total / n).quantize(CENT, rounding=ROUND_HALF_UP)
    parts = [share] * (n - 1)
    parts.append(total - share * (n - 1))
    return [float(p.quantize(CENT, rounding=ROUND_HALF_UP)) for p in parts]
