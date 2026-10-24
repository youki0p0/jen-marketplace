from slugify import slugify


def test_basic():
    assert slugify("Hello World") == "hello-world"


def test_accents_and_punctuation():
    assert slugify("  Héllo,  Wörld!! ") == "hello-world"


def test_symbols():
    assert slugify("C++ & Python 3.12") == "c-python-3-12"


def test_only_separators():
    assert slugify("---") == ""
    assert slugify("") == ""


def test_non_ascii_dropped():
    assert slugify("日本語 text") == "text"


def test_max_length_not_needed():
    assert slugify("naïve café", max_length=20) == "naive-cafe"


def test_max_length_drops_partial_word():
    assert slugify("the quick brown fox", max_length=12) == "the-quick"


def test_max_length_on_boundary():
    assert slugify("the quick brown fox", max_length=9) == "the-quick"


def test_max_length_single_long_word():
    assert slugify("supercalifragilistic", max_length=5) == "super"



def test_hidden_extra():
    assert slugify("A--B", max_length=3) == "a-b"
    assert slugify("Ünïcödé") == "unicode"
    assert slugify("hello world", max_length=8) == "hello"
    assert slugify("ab cd", max_length=3) == "ab"
