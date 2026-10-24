"""Money helpers. See README.md for the specification."""

from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("0.01")


def to_cents(amount):
    if Decimal(str(amount)) < 0:
        raise ValueError("amount must not be negative")
    cents = Decimal(str(amount)) * 100
    return int(cents.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def apply_tax(amount, rate_pct):
    if amount < 0 or rate_pct < 0:
        raise ValueError("amount and rate_pct must not be negative")
    total = Decimal(str(amount)) * (1 + Decimal(str(rate_pct)) / 100)
    return float(total.quantize(CENT, rounding=ROUND_HALF_UP))


def split_bill(total, n):
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        raise ValueError("n must be an int >= 1")
    total = Decimal(str(total))
    share = (total / n).quantize(CENT, rounding=ROUND_HALF_UP)
    parts = [share] * (n - 1)
    parts.append(total - share * (n - 1))
    return [float(p) for p in parts]
