"""Money helpers. See README.md for the specification."""

from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("0.01")


def to_cents(amount):
    value = Decimal(str(amount))
    if value < 0:
        raise ValueError("amount must not be negative")
    return int((value * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def apply_tax(amount, rate_pct):
    value = Decimal(str(amount))
    rate = Decimal(str(rate_pct))
    if value < 0 or rate < 0:
        raise ValueError("amount and rate_pct must not be negative")
    total = value * (1 + rate / 100)
    return float(total.quantize(CENT, rounding=ROUND_HALF_UP))


def split_bill(total, n):
    if not isinstance(n, int) or isinstance(n, bool) or n < 1:
        raise ValueError("n must be an int >= 1")
    value = Decimal(str(total))
    share = (value / n).quantize(CENT, rounding=ROUND_HALF_UP)
    parts = [float(share)] * (n - 1)
    parts.append(float(value - share * (n - 1)))
    return parts
