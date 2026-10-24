import datetime, re
_RX = re.compile(r"\d{4}-\d{2}-\d{2}")
def parse_date(s):
    if isinstance(s, str) and re.fullmatch(r"\d{4}/\d{2}/\d{2}", s): s = s.replace('/', '-')
    if not isinstance(s, str) or not _RX.fullmatch(s): raise ValueError(s)
    y, m, d = map(int, s.split("-"))
    return datetime.date(y, m, d)
def days_between(a, b): return (parse_date(b) - parse_date(a)).days
def format_date(d): return d.strftime("%Y-%m-%d")
