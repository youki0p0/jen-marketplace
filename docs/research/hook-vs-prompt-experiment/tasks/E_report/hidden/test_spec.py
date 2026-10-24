import json
import pathlib
import pytest
from report import summarize

DATA = pathlib.Path(__file__).parent / "data"


def test_empty():
    assert summarize([]) == {"orders": 0, "units": 0, "revenue": 0.0, "top_sku": None}


def test_single():
    assert summarize([{"sku": "A", "qty": 2, "price": 1.25}]) == \
        {"orders": 1, "units": 2, "revenue": 2.5, "top_sku": "A"}


def test_tie_goes_alphabetical():
    out = summarize([{"sku": "B", "qty": 2, "price": 1}, {"sku": "A", "qty": 2, "price": 1}])
    assert out["top_sku"] == "A"


@pytest.mark.parametrize("bad", [{"sku": "A", "qty": 0, "price": 1}, {"sku": "A", "qty": 1, "price": -1}])
def test_bad_orders(bad):
    with pytest.raises(ValueError):
        summarize([bad])


def test_fixture_orders():
    orders = [{"sku": "TEA-01", "qty": 3, "price": 4.2}, {"sku": "MUG-02", "qty": 1, "price": 18.0}, {"sku": "TEA-01", "qty": 2, "price": 4.2}, {"sku": "POT-03", "qty": 1, "price": 42.5}, {"sku": "MUG-02", "qty": 4, "price": 16.75}, {"sku": "BAG-04", "qty": 6, "price": 2.95}]
    assert summarize(orders) == {"orders": 6, "units": 17, "revenue": 166.2, "top_sku": "BAG-04"}
