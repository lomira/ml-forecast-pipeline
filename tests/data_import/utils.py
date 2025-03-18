import pytest
import numpy as np
import pandas as pd
from datetime import timedelta

# * Fixtures for temp csv file creation


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


# * Fixtures for mocking the openmeteo API client


class MockHourlyVariable:
    def __init__(self, values):
        self.values = values

    def ValuesAsNumpy(self):
        return np.array(self.values)


class MockHourly:
    def __init__(self, variables):
        self.variables = variables

    def Variables(self, index):
        return MockHourlyVariable(self.variables[index])


class MockResponse:
    def __init__(self, hourly_data):
        self._hourly = MockHourly(hourly_data)

    def Hourly(self):
        return self._hourly


# Define a fixture for the mock client
@pytest.fixture
def mock_openmeteo_client(monkeypatch):
    # Create a mock client
    class MockClient:
        def __init__(self):
            self.first_call = None
            self.last_call = None

        def weather_api(self, url, params=None):
            if self.first_call is None:
                self.first_call = {"url": url, "params": params}
            self.last_call = {"url": url, "params": params}

            # Extract parameters
            start_date = pd.to_datetime(params.get("start_date"))
            end_date = pd.to_datetime(params.get("end_date"))
            hourly_variables = params.get("hourly", [])

            # Calculate number of hours
            day_range_in_hours = pd.date_range(
                start=start_date, end=end_date + timedelta(hours=23), freq="h"
            )
            num_hours = len(day_range_in_hours)

            # Generate deterministic data for each variable
            hourly_data = []
            for variable in hourly_variables:
                if variable == "temperature_2m":
                    values = [20.0 + (i % 10) for i in range(num_hours)]
                elif variable == "precipitation":
                    values = [0.0 if i % 6 != 0 else 1.5 for i in range(num_hours)]
                else:
                    values = [float(i % 100) for i in range(num_hours)]
                hourly_data.append(values)

            return [MockResponse(hourly_data)]

    # Create instance
    mock_client = MockClient()

    # Patch the setup function
    monkeypatch.setattr(
        "src.data_import.weather.setup_openmeteo_client", lambda: mock_client
    )

    return mock_client
