"""URL slug generation. See README.md for the specification."""
import re
import unicodedata


def slugify(text, max_length=None):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    if max_length is not None and len(slug) > max_length:
        cut = slug[:max_length]
        if cut and slug[max_length].isalnum() and cut[-1].isalnum():
            # the cut split a word: drop the partial word
            cut = cut[: cut.rfind("-") + 1] if "-" in cut else ""
        cut = cut.rstrip("-")
        if not cut:
            cut = slug[:max_length].rstrip("-")
        slug = cut
    return slug
