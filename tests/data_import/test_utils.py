import pytest


@pytest.fixture
def test_csv(tmp_path):
    """
    Creates a temporary CSV file from the provided data string.
    Returns a callable that accepts the CSV data and writes it to a file.
    """

    def _write_csv(data: str):
        csv_file = tmp_path / "temp.csv"
        csv_file.write_text(data)
        return csv_file

    return _write_csv
