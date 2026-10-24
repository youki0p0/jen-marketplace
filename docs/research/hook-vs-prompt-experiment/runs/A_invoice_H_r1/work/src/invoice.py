"""Invoice line calculations. See README.md for the specification."""
from decimal import Decimal, ROUND_HALF_UP

_CENT = Decimal("0.01")


def _line_decimal(unit_price, qty, discount_pct=0.0):
    if not isinstance(qty, int) or isinstance(qty, bool) or qty < 1:
        raise ValueError("qty must be an int >= 1")
    price = Decimal(str(unit_price))
    pct = Decimal(str(discount_pct))
    if not 0 <= pct <= 100:
        raise ValueError("discount_pct must be between 0 and 100")
    if price < 0:
        raise ValueError("unit_price must be >= 0")
    total = price * Decimal(str(qty)) * (1 - pct / 100)
    return total.quantize(_CENT, rounding=ROUND_HALF_UP)


def line_total(unit_price, qty, discount_pct=0.0):
    return float(_line_decimal(unit_price, qty, discount_pct))


def invoice_total(lines):
    total = sum((_line_decimal(*line) for line in lines), Decimal("0"))
    return float(total.quantize(_CENT, rounding=ROUND_HALF_UP))
