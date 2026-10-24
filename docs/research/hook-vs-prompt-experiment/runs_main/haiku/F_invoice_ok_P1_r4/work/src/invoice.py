"""Invoice line calculations. See README.md for the specification."""

from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("0.01")


def _quantize(value):
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _line_total_decimal(unit_price, qty, discount_pct=0.0):
    if isinstance(qty, bool) or not isinstance(qty, int) or qty < 1:
        raise ValueError("qty must be an int >= 1")

    pct = Decimal(str(discount_pct))
    if not (Decimal("0") <= pct <= Decimal("100")):
        raise ValueError("discount_pct must be between 0 and 100")

    price = Decimal(str(unit_price))
    if price < 0:
        raise ValueError("unit_price must be >= 0")

    return price * qty * (1 - pct / 100)


def line_total(unit_price, qty, discount_pct=0.0):
    return float(_quantize(_line_total_decimal(unit_price, qty, discount_pct)))


def invoice_total(lines):
    total = sum(
        (_quantize(_line_total_decimal(price, qty, pct)) for price, qty, pct in lines),
        Decimal("0"),
    )
    return float(_quantize(total))
