"""URL slug generation. See README.md for the specification."""

import re
import unicodedata


def slugify(text, max_length=None):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")

    if max_length is not None and len(slug) > max_length:
        cut = slug[:max_length]
        if max_length > 0 and slug[max_length - 1].isalnum() and slug[max_length].isalnum():
            cut = cut.rsplit("-", 1)[0] if "-" in cut else ""
        cut = cut.rstrip("-")
        if not cut:
            cut = slug[:max_length].rstrip("-")
        slug = cut

    return slug
