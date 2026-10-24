"""URL slug generation. See README.md for the specification."""

import re
import unicodedata


def slugify(text, max_length=None):
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")

    if max_length is None or len(slug) <= max_length:
        return slug

    cut = slug[:max_length]
    if cut and slug[max_length - 1].isalnum() and slug[max_length].isalnum():
        idx = cut.rfind("-")
        cut = cut[:idx] if idx != -1 else ""
    cut = cut.rstrip("-")

    if not cut:
        return slug[:max_length].rstrip("-")
    return cut
