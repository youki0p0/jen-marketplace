"""Invoice line calculations. See README.md for the specification."""

from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("0.01")


def _line_amount(unit_price, qty, discount_pct):
    if not isinstance(qty, int) or qty < 1:
        raise ValueError("qty must be an int >= 1")
    price = Decimal(str(unit_price))
    if price < 0:
        raise ValueError("unit_price must be >= 0")
    discount = Decimal(str(discount_pct))
    if not (0 <= discount <= 100):
        raise ValueError("discount_pct must be between 0 and 100")
    amount = price * qty * (1 - discount / 100)
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


def line_total(unit_price, qty, discount_pct=0.0):
    return float(_line_amount(unit_price, qty, discount_pct))


def invoice_total(lines):
    total = sum((_line_amount(*line) for line in lines), Decimal("0"))
    return float(total.quantize(CENT, rounding=ROUND_HALF_UP))
