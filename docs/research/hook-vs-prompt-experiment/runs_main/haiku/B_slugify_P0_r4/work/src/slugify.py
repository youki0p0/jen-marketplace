"""URL slug generation. See README.md for the specification."""

import re
import unicodedata


def slugify(text, max_length=None):
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")

    if max_length is not None and len(slug) > max_length:
        cut = slug[:max_length]
        if cut[-1].isalnum() and slug[max_length].isalnum():
            # The cut split a word, so drop the partial word.
            cut = cut[:cut.rfind("-")] if "-" in cut else ""
        cut = cut.rstrip("-")
        slug = cut if cut else slug[:max_length].rstrip("-")

    return slug
