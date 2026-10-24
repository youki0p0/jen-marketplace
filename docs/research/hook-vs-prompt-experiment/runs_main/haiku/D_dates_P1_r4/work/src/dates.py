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
    try:
        return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        raise ValueError(f"impossible calendar date: {s!r}") from None


def days_between(a, b):
    return (parse_date(b) - parse_date(a)).days


def format_date(d):
    return f"{d.year:04d}-{d.month:02d}-{d.day:02d}"
