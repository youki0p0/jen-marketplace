"""Strict date helpers. See README.md for the specification."""

import datetime
import re

_ISO = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


def parse_date(s):
    if not isinstance(s, str) or not _ISO.fullmatch(s):
        raise ValueError(f"invalid date: {s!r}")
    return datetime.date(int(s[:4]), int(s[5:7]), int(s[8:10]))


def days_between(a, b):
    return (parse_date(b) - parse_date(a)).days


def format_date(d):
    return f"{d.year:04d}-{d.month:02d}-{d.day:02d}"
