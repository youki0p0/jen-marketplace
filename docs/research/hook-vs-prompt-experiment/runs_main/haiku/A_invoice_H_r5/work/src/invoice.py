"""Invoice line calculations. See README.md for the specification."""

from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("0.01")


def _quantize(value):
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def line_total(unit_price, qty, discount_pct=0.0):
    if not isinstance(qty, int) or qty < 1:
        raise ValueError("qty must be an int >= 1")
    if not 0 <= discount_pct <= 100:
        raise ValueError("discount_pct must be between 0 and 100")
    if unit_price < 0:
        raise ValueError("unit_price must be >= 0")

    price = Decimal(str(unit_price))
    discount = Decimal(str(discount_pct))
    factor = Decimal(1) - discount / Decimal(100)
    return float(_quantize(price * qty * factor))


def invoice_total(lines):
    total = sum(
        (Decimal(str(line_total(*line))) for line in lines),
        Decimal(0),
    )
    return float(_quantize(total))
