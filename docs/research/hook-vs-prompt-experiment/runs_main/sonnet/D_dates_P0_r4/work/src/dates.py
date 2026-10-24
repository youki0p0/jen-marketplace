"""Strict date helpers. See README.md for the specification."""
import datetime
import re

_ISO = re.compile(r"([0-9]{4})-([0-9]{2})-([0-9]{2})\Z")


def parse_date(s):
    if not isinstance(s, str):
        raise ValueError("date must be a string")
    m = _ISO.match(s)
    if not m:
        raise ValueError("invalid date format: %r" % (s,))
    return datetime.date(*map(int, m.groups()))


def days_between(a, b):
    return (parse_date(b) - parse_date(a)).days


def format_date(d):
    return "%04d-%02d-%02d" % (d.year, d.month, d.day)
