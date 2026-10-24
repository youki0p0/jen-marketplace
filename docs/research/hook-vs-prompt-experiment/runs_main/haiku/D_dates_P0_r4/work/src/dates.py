"""Strict date helpers. See README.md for the specification."""

import datetime
import re

_ISO_DATE = re.compile(r"([0-9]{4})-([0-9]{2})-([0-9]{2})")


def parse_date(s):
    if not isinstance(s, str):
        raise ValueError("date must be a string, got %r" % (type(s).__name__,))
    match = _ISO_DATE.fullmatch(s)
    if match is None:
        raise ValueError("date must be YYYY-MM-DD, got %r" % (s,))
    year, month, day = (int(part) for part in match.groups())
    # datetime.date raises ValueError for impossible dates such as 2023-02-29.
    return datetime.date(year, month, day)


def days_between(a, b):
    return (parse_date(b) - parse_date(a)).days


def format_date(d):
    return d.strftime("%Y-%m-%d")
