"""URL slug generation. See README.md for the specification."""

import re
import unicodedata


def slugify(text, max_length=None):
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")

    if max_length is not None and len(slug) > max_length:
        cut = slug[:max_length]
        before = slug[max_length - 1]
        after = slug[max_length]
        if before.isalnum() and after.isalnum():
            cut = cut.rsplit("-", 1)[0] if "-" in cut else ""
        shortened = cut.rstrip("-")
        slug = shortened if shortened else slug[:max_length].rstrip("-")

    return slug
