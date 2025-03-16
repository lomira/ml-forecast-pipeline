import pytest
from src.data_import.weather import get_missing_date_ranges


def test_no_overlap_after():
    assert get_missing_date_ranges(
        available_start="2023-02-01",
        available_end="2023-02-10",
        requested_start="2023-03-01",
        requested_end="2023-03-10",
    ) == [("2023-02-11", "2023-03-10")]


def test_no_overlap_before():
    assert get_missing_date_ranges(
        available_start="2023-03-01",
        available_end="2023-03-10",
        requested_start="2023-02-01",
        requested_end="2023-02-10",
    ) == [("2023-02-01", "2023-02-28")]


def test_partial_overlap_before():
    assert get_missing_date_ranges(
        available_start="2023-02-05",
        available_end="2023-02-15",
        requested_start="2023-02-01",
        requested_end="2023-02-10",
    ) == [("2023-02-01", "2023-02-04")]


def test_partial_overlap_after():
    assert get_missing_date_ranges(
        available_start="2023-02-05",
        available_end="2023-02-15",
        requested_start="2023-02-10",
        requested_end="2023-02-20",
    ) == [("2023-02-16", "2023-02-20")]


def test_requested_range_fully_contains_available():
    assert get_missing_date_ranges(
        available_start="2023-02-05",
        available_end="2023-02-10",
        requested_start="2023-02-01",
        requested_end="2023-02-15",
    ) == [("2023-02-01", "2023-02-04"), ("2023-02-11", "2023-02-15")]


def test_available_range_fully_contains_requested():
    assert (
        get_missing_date_ranges(
            available_start="2023-02-01",
            available_end="2023-02-15",
            requested_start="2023-02-05",
            requested_end="2023-02-10",
        )
        == []
    )


def test_identical_ranges():
    assert (
        get_missing_date_ranges(
            available_start="2023-02-01",
            available_end="2023-02-10",
            requested_start="2023-02-01",
            requested_end="2023-02-10",
        )
        == []
    )


def test_edge_case_requested_start_one_day_before_available_start():
    assert get_missing_date_ranges(
        available_start="2023-02-02",
        available_end="2023-02-10",
        requested_start="2023-02-01",
        requested_end="2023-02-10",
    ) == [("2023-02-01", "2023-02-01")]


def test_edge_case_requested_end_one_day_after_available_end():
    assert get_missing_date_ranges(
        available_start="2023-02-01",
        available_end="2023-02-09",
        requested_start="2023-02-01",
        requested_end="2023-02-10",
    ) == [("2023-02-10", "2023-02-10")]


def test_requested_range_completely_before_available():
    assert get_missing_date_ranges(
        available_start="2023-02-01",
        available_end="2023-02-10",
        requested_start="2023-01-15",
        requested_end="2023-01-20",
    ) == [("2023-01-15", "2023-01-31")]


def test_requested_range_completely_after_available():
    assert get_missing_date_ranges(
        available_start="2023-02-01",
        available_end="2023-02-10",
        requested_start="2023-02-15",
        requested_end="2023-02-20",
    ) == [("2023-02-11", "2023-02-20")]


def test_requested_range_before_and_after_available():
    assert get_missing_date_ranges(
        available_start="2023-02-05",
        available_end="2023-02-10",
        requested_start="2023-02-01",
        requested_end="2023-02-15",
    ) == [("2023-02-01", "2023-02-04"), ("2023-02-11", "2023-02-15")]


def test_available_start_equal_requested_end():
    assert get_missing_date_ranges(
        available_start="2023-02-10",
        available_end="2023-02-20",
        requested_start="2023-02-01",
        requested_end="2023-02-10",
    ) == [("2023-02-01", "2023-02-09")]


def test_available_end_equal_requested_start():
    assert get_missing_date_ranges(
        available_start="2023-02-01",
        available_end="2023-02-10",
        requested_start="2023-02-10",
        requested_end="2023-02-20",
    ) == [("2023-02-11", "2023-02-20")]


def test_invalid_available_range():
    with pytest.raises(ValueError):
        get_missing_date_ranges(
            available_start="2023-02-10",
            available_end="2023-02-01",
            requested_start="2023-01-01",
            requested_end="2023-01-10",
        )


def test_invalid_requested_range():
    with pytest.raises(ValueError):
        get_missing_date_ranges(
            available_start="2023-01-01",
            available_end="2023-01-10",
            requested_start="2023-01-10",
            requested_end="2023-01-01",
        )
