"""Strict date helpers. See README.md for the specification."""

import datetime
import re

_ISO_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


def parse_date(s):
    if not isinstance(s, str) or not _ISO_DATE.fullmatch(s):
        raise ValueError(f"not a YYYY-MM-DD date: {s!r}")
    return datetime.date(int(s[0:4]), int(s[5:7]), int(s[8:10]))


def days_between(a, b):
    return (parse_date(b) - parse_date(a)).days


def format_date(d):
    return d.strftime("%Y-%m-%d")
