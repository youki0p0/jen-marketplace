"""Strict date helpers. See README.md for the specification."""

import datetime
import re

_ISO_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


def parse_date(s):
    if not isinstance(s, str) or not _ISO_DATE.fullmatch(s):
        raise ValueError(f"expected YYYY-MM-DD, got {s!r}")
    year, month, day = (int(part) for part in s.split("-"))
    return datetime.date(year, month, day)


def days_between(a, b):
    return (parse_date(b) - parse_date(a)).days


def format_date(d):
    return d.strftime("%Y-%m-%d")
