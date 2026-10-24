"""URL slug generation. See README.md for the specification."""

import re
import unicodedata


def slugify(text, max_length=None):
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")

    if max_length is None or len(slug) <= max_length:
        return slug

    head = slug[:max_length]
    split_word = slug[max_length - 1].isalnum() and slug[max_length].isalnum()
    if split_word:
        head = head.rsplit("-", 1)[0] if "-" in head else ""
    head = head.rstrip("-")

    if not head:
        head = slug[:max_length].rstrip("-")
    return head
