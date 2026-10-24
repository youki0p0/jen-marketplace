# money

Implement the three functions in `src/money.py`.

**All rounding in this module uses `ROUND_HALF_UP` from the `decimal` module.**
Convert every numeric input with `Decimal(str(x))` before doing arithmetic.

## `to_cents(amount) -> int`
Returns `amount` in whole cents, rounded with ROUND_HALF_UP. Raises `ValueError` if `amount` is negative.

## `apply_tax(amount, rate_pct) -> float`
Returns `amount × (1 + rate_pct / 100)`, rounded to 2 decimal places with ROUND_HALF_UP.
Raises `ValueError` if `amount` or `rate_pct` is negative.

## `split_bill(total, n) -> list[float]`
Splits `total` into `n` parts. Every part except the last is `total / n` rounded to 2 decimal
places with ROUND_HALF_UP; the last part is whatever remains, so the parts always sum exactly
to `total`. `n` must be an `int >= 1`, otherwise raise `ValueError`.

## Running the tests

    python3 -m pytest -q
