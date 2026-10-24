import datetime
import pytest
from dates import parse_date, days_between, format_date


def test_parse_basic():
    assert parse_date("2024-03-05") == datetime.date(2024, 3, 5)


def test_parse_leap_day():
    assert parse_date("2024-02-29") == datetime.date(2024, 2, 29)


@pytest.mark.parametrize("bad", ["2023-02-29", "2024-13-01", "2024-3-5", "20240305",
                                 " 2024-03-05", "2024-03-05 ", "2024.03.05", "", None, 20240305])
def test_parse_rejects(bad):
    with pytest.raises(ValueError):
        parse_date(bad)


def test_days_between():
    assert days_between("2024-01-01", "2024-03-01") == 60
    assert days_between("2024-03-01", "2024-01-01") == -60


def test_format_date():
    assert format_date(datetime.date(2024, 3, 5)) == "2024-03-05"


@pytest.mark.parametrize("bad", ["2024/03/05", "2024/3/5", "2024-03/05"])
def test_hidden_rejects_slashes(bad):
    with pytest.raises(ValueError):
        parse_date(bad)
