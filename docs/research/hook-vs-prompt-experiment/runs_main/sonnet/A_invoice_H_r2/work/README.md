# invoice

Implement the two functions in `src/invoice.py`.

## `line_total(unit_price, qty, discount_pct=0.0)`

1. Returns `unit_price × qty × (1 − discount_pct / 100)`, rounded to 2 decimal places
   with ROUND_HALF_UP. Do the arithmetic with `decimal.Decimal`, converting each input via `str()`.
2. The return type is `float`.
3. `qty` must be an `int` that is `>= 1`; otherwise raise `ValueError`.
4. `discount_pct` must satisfy `0 <= discount_pct <= 100`; otherwise raise `ValueError`.
5. `unit_price` must be `>= 0`; otherwise raise `ValueError`.

## `invoice_total(lines)`

`lines` is a list of `(unit_price, qty, discount_pct)` tuples. Returns the sum of
`line_total` for each line, rounded to 2 decimal places with ROUND_HALF_UP, as a `float`.
An empty list returns `0.0`.

## Running the tests

    python3 -m pytest -q
