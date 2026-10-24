"""URL slug generation. See README.md for the specification."""
import re
import unicodedata


def slugify(text, max_length=None):
    s = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    if max_length is not None and len(s) > max_length:
        cut = s[:max_length]
        if cut and s[max_length - 1].isalnum() and s[max_length].isalnum():
            cut = cut[:cut.rfind("-") + 1] if "-" in cut else ""
        cut = cut.rstrip("-")
        if not cut:
            cut = s[:max_length].rstrip("-")
        s = cut
    return s
