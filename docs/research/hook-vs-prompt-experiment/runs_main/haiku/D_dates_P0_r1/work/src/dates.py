"""Strict date helpers. See README.md for the specification."""

import datetime
import re

_ISO_DATE = re.compile(r"([0-9]{4})-([0-9]{2})-([0-9]{2})")


def parse_date(s):
    if not isinstance(s, str):
        raise ValueError(f"expected a string, got {type(s).__name__}")
    m = _ISO_DATE.fullmatch(s)
    if m is None:
        raise ValueError(f"not an ISO 8601 date (YYYY-MM-DD): {s!r}")
    year, month, day = (int(g) for g in m.groups())
    # datetime.date raises ValueError for impossible dates such as 2023-02-29.
    return datetime.date(year, month, day)


def days_between(a, b):
    return (parse_date(b) - parse_date(a)).days


def format_date(d):
    return d.strftime("%Y-%m-%d")
