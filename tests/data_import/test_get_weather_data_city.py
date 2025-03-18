import pytest
import pandas as pd
import numpy as np
from datetime import timedelta
from src.data_import.weather import (
    get_weather_data_city,
    fetch_weather_city_from_api,
)


# Create the necessary mocks
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
            self.last_call = None

        def weather_api(self, url, params=None):
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


# Test the function
def test_fetch_weather_city_from_api(mock_openmeteo_client):
    # Import the function to test

    # Test data
    city = {"name": "New York", "latitude": 40.7128, "longitude": -74.0060}
    date_range = ["2023-06-01", "2023-06-02"]
    hourly_variables = ["temperature_2m", "precipitation", "windspeed_10m"]
    timezone = "America/New_York"

    # Call the function
    result = fetch_weather_city_from_api(city, date_range, hourly_variables, timezone)

    # Verify the result is a DataFrame with expected properties
    assert isinstance(result, pd.DataFrame)
    assert "city" in result.columns
    assert result["city"].iloc[0] == "New York"

    # Check all variables are in the result
    for variable in hourly_variables:
        assert variable in result.columns

    # Verify the API was called with correct parameters
    assert mock_openmeteo_client.last_call is not None
    call_params = mock_openmeteo_client.last_call["params"]
    assert call_params["latitude"] == city["latitude"]
    assert call_params["longitude"] == city["longitude"]
    assert call_params["hourly"] == hourly_variables

    # Check we have the expected number of hours (2 days = 48 hours)
    assert len(result) == 48


# Test with different parameters
def test_fetch_weather_single_day(mock_openmeteo_client):

    city = {"name": "Tunis", "latitude": 86.819, "longitude": 10.1658}
    result = get_weather_data_city(
        city,
        start_date="2023-01-01",
        end_date="2023-01-01",
        hourly_variables=["temperature_2m", "relative_humidity_2m"],
        timezone="Africa/Tunis",
    )

    # Should have 24 hours for a single day
    assert len(result) == 24
    assert "temperature_2m" in result.columns
