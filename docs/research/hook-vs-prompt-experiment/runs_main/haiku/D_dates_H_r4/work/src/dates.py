"""Strict date helpers. See README.md for the specification."""

import datetime
import re

_ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


def parse_date(s):
    if not isinstance(s, str) or not _ISO_DATE.fullmatch(s):
        raise ValueError(f"expected YYYY-MM-DD, got {s!r}")
    try:
        return datetime.datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"impossible date: {s!r}") from None


def days_between(a, b):
    return (parse_date(b) - parse_date(a)).days


def format_date(d):
    return d.strftime("%Y-%m-%d")
