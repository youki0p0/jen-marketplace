"""Invoice line calculations. See README.md for the specification."""

from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("0.01")


def line_total(unit_price, qty, discount_pct=0.0):
    if isinstance(qty, bool) or not isinstance(qty, int) or qty < 1:
        raise ValueError("qty must be an int >= 1")
    if not 0 <= discount_pct <= 100:
        raise ValueError("discount_pct must be between 0 and 100")
    if unit_price < 0:
        raise ValueError("unit_price must be >= 0")

    price = Decimal(str(unit_price))
    discount = Decimal(str(discount_pct))
    total = price * qty * (1 - discount / 100)
    return float(total.quantize(CENT, rounding=ROUND_HALF_UP))


def invoice_total(lines):
    total = Decimal("0")
    for unit_price, qty, discount_pct in lines:
        total += Decimal(str(line_total(unit_price, qty, discount_pct)))
    return float(total.quantize(CENT, rounding=ROUND_HALF_UP))
