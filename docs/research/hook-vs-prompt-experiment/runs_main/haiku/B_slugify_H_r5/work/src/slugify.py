"""URL slug generation. See README.md for the specification."""

import re
import unicodedata


def slugify(text, max_length=None):
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")

    if max_length is not None and len(slug) > max_length:
        cut = slug[:max_length]
        split_word = (
            cut
            and cut[-1].isalnum()
            and slug[max_length].isalnum()
        )
        if split_word:
            cut = cut.rpartition("-")[0]
        trimmed = cut.rstrip("-")
        if trimmed:
            return trimmed
        return slug[:max_length].rstrip("-")

    return slug
