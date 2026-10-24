"""URL slug generation. See README.md for the specification."""

import re
import unicodedata


def slugify(text, max_length=None):
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", text).strip("-")

    if max_length is not None and len(slug) > max_length:
        cut = slug[:max_length]
        split_word = cut[-1:].isalnum() and slug[max_length:max_length + 1].isalnum()
        if split_word:
            cut = re.sub(r"[a-z0-9]+$", "", cut)
        trimmed = cut.rstrip("-")
        if trimmed:
            slug = trimmed
        else:
            slug = slug[:max_length].rstrip("-")

    return slug
