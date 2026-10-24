# slugify

Implement `slugify(text, max_length=None)` in `src/slugify.py`.

1. Normalize `text` with `unicodedata.normalize("NFKD", ...)` and drop every non-ASCII character.
2. Lowercase it.
3. Replace each run of characters that are not `a-z` or `0-9` with a single `-`.
4. Strip leading and trailing `-`.
5. If `max_length` is given and the slug is longer than `max_length`:
   - cut it to the first `max_length` characters;
   - if the cut split a word (the character just before the cut and the character just
     after it are both alphanumeric), drop that partial word;
   - strip trailing `-`;
   - if this leaves an empty string, return the first `max_length` characters of the
     slug instead, with trailing `-` stripped.
6. If nothing is left, return `""`.

## Running the tests

    python3 -m pytest -q
