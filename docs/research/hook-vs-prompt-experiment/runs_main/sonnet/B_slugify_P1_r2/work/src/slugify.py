"""URL slug generation. See README.md for the specification."""
import re
import unicodedata


def slugify(text, max_length=None):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    if max_length is not None and len(slug) > max_length:
        cut = slug[:max_length]
        if cut and slug[max_length - 1].isalnum() and slug[max_length].isalnum():
            head = cut.rsplit("-", 1)[0] if "-" in cut else ""
            result = head.rstrip("-")
        else:
            result = cut.rstrip("-")
        slug = result or cut.rstrip("-")
    return slug
