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
    orders = json.loads((DATA / "orders.json").read_text())
    expected = json.loads((DATA / "expected_summary.json").read_text())
    assert summarize(orders) == expected
