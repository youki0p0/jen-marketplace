"""Invoice line calculations. See README.md for the specification."""


def line_total(unit_price, qty, discount_pct=0.0):
    raise NotImplementedError


def invoice_total(lines):
    raise NotImplementedError
