import pytest
import pandas as pd
from tests.data_import.utils import test_csv
from src.data_import.import_y import import_y


def test_valid_import(test_csv):
    """Test successful import with valid data"""
    data = "date;value\n01/01/2023;10\n02/01/2023;20\n03/01/2023;30"
    filepath = test_csv(data)
    df = import_y(filepath)

    assert df is not None
    assert len(df) == 3
    assert list(df.columns) == ["date", "y"]
    assert isinstance(df["date"].iloc[0], pd.Timestamp)
    assert df["y"].iloc[0] == 10


def test_decimal_values(test_csv):
    """Test with decimal values in second column"""
    data = "date;value\n01/01/2023;10.5\n02/01/2023;20.75\n03/01/2023;30.25"
    filepath = test_csv(data)
    df = import_y(filepath)

    assert df is not None
    assert df["y"].iloc[0] == 10.5
    assert df["y"].iloc[1] == 20.75


def test_wrong_separator_date(test_csv):
    """Test with wrong date separator (hyphen instead of slash)"""
    data = "date;value\n01-01-2023;10\n02-01-2023;20\n03-01-2023;30"
    filepath = test_csv(data)
    with pytest.raises(ValueError):
        import_y(filepath)


def test_wrong_format_date(test_csv):
    """Test with wrong date format (year first)"""
    data = "date;value\n2023/01/01;10\n2023/01/02;20\n2023/01/03;30"
    filepath = test_csv(data)
    with pytest.raises(ValueError):
        import_y(filepath)


def test_mixed_date_formats(test_csv):
    """Test with mixed date formats"""
    data = "date;value\n01/01/2023;10\n2023/01/02;20\n03/01/2023;30"
    filepath = test_csv(data)
    with pytest.raises(ValueError):
        import_y(filepath)


def test_invalid_date(test_csv):
    """Test with invalid date"""
    data = "date;value\n32/01/2023;10\n02/01/2023;20"
    filepath = test_csv(data)
    with pytest.raises(ValueError):
        import_y(filepath)


def test_invalid_numeric_data(test_csv):
    """Test with non-numeric values in second column"""
    data = "date;value\n01/01/2023;ten\n02/01/2023;20\n03/01/2023;30"
    filepath = test_csv(data)
    with pytest.raises(ValueError):
        import_y(filepath)


def test_missing_file():
    """Test with non-existent file"""
    result = import_y("nonexistent_file.csv")
    assert result is None


def test_wrong_columns(test_csv):
    """Test with wrong number of columns"""
    data = "date;value;extra\n01/01/2023;10;xyz\n02/01/2023;20;abc"
    filepath = test_csv(data)
    with pytest.raises(ValueError):
        import_y(filepath)


def test_empty_file(test_csv):
    """Test with empty file"""
    data = ""
    filepath = test_csv(data)
    with pytest.raises(Exception):
        import_y(filepath)
