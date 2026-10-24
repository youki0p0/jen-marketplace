"""URL slug generation. See README.md for the specification."""

import re
import unicodedata


def slugify(text, max_length=None):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    if max_length is not None and len(slug) > max_length:
        cut = slug[:max_length]
        if cut and cut[-1] != "-" and slug[max_length] != "-":
            cut = cut[: cut.rfind("-") + 1]
        cut = cut.rstrip("-")
        slug = cut or slug[:max_length].rstrip("-")
    return slug
