import pytest
from money import to_cents, apply_tax, split_bill


def test_to_cents_basic():
    assert to_cents(12.34) == 1234
    assert to_cents("0") == 0


def test_to_cents_rounds_half_up():
    assert to_cents("0.125") == 13
    assert to_cents("2.675") == 268


def test_to_cents_negative():
    with pytest.raises(ValueError):
        to_cents(-1)


def test_apply_tax_basic():
    assert apply_tax(100, 10) == 110.00
    assert apply_tax(19.99, 8) == 21.59


def test_apply_tax_negative():
    with pytest.raises(ValueError):
        apply_tax(-1, 5)
    with pytest.raises(ValueError):
        apply_tax(1, -5)


def test_split_bill_even():
    assert split_bill(30, 3) == [10.00, 10.00, 10.00]


def test_split_bill_remainder_goes_last():
    assert split_bill(10, 3) == [3.33, 3.33, 3.34]
    assert sum(split_bill(10, 3)) == pytest.approx(10.00)


@pytest.mark.parametrize("n", [0, -2, 1.5])
def test_split_bill_bad_n(n):
    with pytest.raises(ValueError):
        split_bill(10, n)


def test_apply_tax_tie():
    # Tax amounts are rounded the way the tax office does it.
    assert apply_tax(2.50, 5) == 2.62
