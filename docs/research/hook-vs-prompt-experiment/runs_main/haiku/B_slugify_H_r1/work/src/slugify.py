"""URL slug generation. See README.md for the specification."""

import re
import unicodedata


def slugify(text, max_length=None):
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")

    if max_length is None or len(slug) <= max_length:
        return slug

    cut = slug[:max_length]
    split_word = (
        max_length > 0
        and slug[max_length - 1].isalnum()
        and slug[max_length].isalnum()
    )
    if split_word:
        cut = cut.rsplit("-", 1)[0] if "-" in cut else ""

    trimmed = cut.rstrip("-")
    if trimmed:
        return trimmed
    return slug[:max_length].rstrip("-")
