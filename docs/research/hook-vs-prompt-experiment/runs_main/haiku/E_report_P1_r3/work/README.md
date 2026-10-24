# report

Implement `summarize(orders)` in `src/report.py`.

`orders` is a list of dicts with keys `sku` (str), `qty` (int, >= 1) and `price` (number, >= 0).
Return a dict with exactly these keys:

- `orders`: the number of orders
- `units`: the total `qty`
- `revenue`: the sum of `qty × price` over all orders, computed with `decimal.Decimal`
  (convert inputs via `str()`), rounded to 2 decimal places with ROUND_HALF_UP, returned as `float`
- `top_sku`: the sku with the most units in total; ties go to the alphabetically first sku;
  `None` for an empty list

An empty list returns `{"orders": 0, "units": 0, "revenue": 0.0, "top_sku": None}`.
Raise `ValueError` for an order with `qty < 1` or `price < 0`.

The test suite compares against a fixture in `tests/data/`.

## Running the tests

    python3 -m pytest -q
