"""Strict date helpers. See README.md for the specification."""

import datetime
import re

_ISO_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


def parse_date(s):
    if not isinstance(s, str) or not _ISO_DATE.fullmatch(s):
        raise ValueError(f"not an ISO 8601 date (YYYY-MM-DD): {s!r}")
    year, month, day = (int(part) for part in s.split("-"))
    return datetime.date(year, month, day)


def days_between(a, b):
    return (parse_date(b) - parse_date(a)).days


def format_date(d):
    return f"{d.year:04d}-{d.month:02d}-{d.day:02d}"
