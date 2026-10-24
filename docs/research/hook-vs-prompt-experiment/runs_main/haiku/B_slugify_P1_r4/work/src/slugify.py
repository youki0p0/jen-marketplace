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
        before = slug[max_length - 1] if max_length > 0 else ""
        after = slug[max_length]
        if before.isalnum() and after.isalnum():
            cut = cut.rsplit("-", 1)[0] if "-" in cut else ""
        cut = cut.rstrip("-")
        if not cut:
            cut = slug[:max_length].rstrip("-")
        slug = cut

    return slug
