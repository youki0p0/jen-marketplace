import pytest
from invoice import line_total, invoice_total


def test_basic():
    assert line_total(10.0, 2) == 20.00


def test_discount():
    assert line_total(20.0, 2, 10) == 36.00


def test_discount_three_items():
    assert line_total(10.0, 3, 10) == 27.00


def test_rounding_half_up():
    assert line_total(0.125, 1) == 0.13
    assert line_total(1.005, 1) == 1.01


def test_full_discount():
    assert line_total(50, 4, 100) == 0.0


def test_return_type():
    assert isinstance(line_total(3, 1), float)


@pytest.mark.parametrize("qty", [0, -1, 2.5])
def test_bad_qty(qty):
    with pytest.raises(ValueError):
        line_total(10.0, qty)


@pytest.mark.parametrize("pct", [-1, 101])
def test_bad_discount(pct):
    with pytest.raises(ValueError):
        line_total(10.0, 1, pct)


def test_bad_price():
    with pytest.raises(ValueError):
        line_total(-0.01, 1)


def test_invoice_total():
    assert invoice_total([(10.0, 2, 0), (20.0, 2, 10)]) == 56.00


def test_invoice_empty():
    assert invoice_total([]) == 0.0
