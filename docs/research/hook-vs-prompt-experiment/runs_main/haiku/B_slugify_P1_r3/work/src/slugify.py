"""URL slug generation. See README.md for the specification."""

import re
import unicodedata


def slugify(text, max_length=None):
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")

    if max_length is not None and len(slug) > max_length:
        prefix = slug[:max_length]
        cut = prefix
        if slug[max_length - 1].isalnum() and slug[max_length].isalnum():
            # The cut split a word, so drop the partial word.
            idx = cut.rfind("-")
            cut = cut[:idx] if idx >= 0 else ""
        slug = cut.rstrip("-") or prefix.rstrip("-")
    return slug
