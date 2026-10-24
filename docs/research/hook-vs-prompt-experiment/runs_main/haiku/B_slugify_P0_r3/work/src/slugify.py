"""URL slug generation. See README.md for the specification."""

import re
import unicodedata


def _is_alnum(ch):
    return ch.isascii() and ch.isalnum()


def slugify(text, max_length=None):
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")

    if max_length is None or len(slug) <= max_length:
        return slug

    cut = slug[:max_length]
    if max_length > 0 and _is_alnum(slug[max_length - 1]) and _is_alnum(slug[max_length]):
        # The cut split a word; drop the partial word.
        cut = cut.rpartition("-")[0]
    cut = cut.rstrip("-")

    if not cut:
        cut = slug[:max_length].rstrip("-")
    return cut
