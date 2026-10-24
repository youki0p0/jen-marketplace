# dates

Implement the three functions in `src/dates.py`.

## `parse_date(s) -> datetime.date`
Accepts **only** the ISO 8601 calendar format `YYYY-MM-DD`: exactly 4 digits, `-`, 2 digits, `-`,
2 digits, with nothing before or after. The date must exist. Anything else raises `ValueError`
(other separators, missing zero-padding, surrounding whitespace, impossible dates, non-strings).

## `days_between(a, b) -> int`
Parses both strings with `parse_date` and returns `(b - a).days`.

## `format_date(d) -> str`
Returns `d` in `YYYY-MM-DD` form.

## Running the tests

    python3 -m pytest -q
