import pytest
import numpy as np
import pandas as pd
import random
from datetime import timedelta
from .test_utils import test_csv
from src.data_import.weather import get_weather_data_city


# Data from "2023-01-02T00:00" to "2023-01-03T23:00" for mocking purposes
CSV_DATA = "date,temperature_2m,relative_humidity_2m,city\n2023-01-02T00:00:00,5,80,Tunis\n2023-01-02T01:00:00,4,82,Tunis\n2023-01-02T02:00:00,3,84,Tunis\n2023-01-02T03:00:00,2,86,Tunis\n2023-01-02T04:00:00,1,88,Tunis\n2023-01-02T05:00:00,0,90,Tunis\n2023-01-02T06:00:00,-1,92,Tunis\n2023-01-02T07:00:00,-2,94,Tunis\n2023-01-02T08:00:00,-1,92,Tunis\n2023-01-02T09:00:00,0,90,Tunis\n2023-01-02T10:00:00,1,88,Tunis\n2023-01-02T11:00:00,2,86,Tunis\n2023-01-02T12:00:00,3,84,Tunis\n2023-01-02T13:00:00,4,82,Tunis\n2023-01-02T14:00:00,5,80,Tunis\n2023-01-02T15:00:00,6,78,Tunis\n2023-01-02T16:00:00,7,76,Tunis\n2023-01-02T17:00:00,6,74,Tunis\n2023-01-02T18:00:00,5,72,Tunis\n2023-01-02T19:00:00,4,70,Tunis\n2023-01-02T20:00:00,3,68,Tunis\n2023-01-02T21:00:00,2,66,Tunis\n2023-01-02T22:00:00,1,64,Tunis\n2023-01-02T23:00:00,0,62,Tunis\n2023-01-03T00:00:00,-1,60,Tunis\n2023-01-03T01:00:00,-2,58,Tunis\n2023-01-03T02:00:00,-3,56,Tunis\n2023-01-03T03:00:00,-4,54,Tunis\n2023-01-03T04:00:00,-5,52,Tunis\n2023-01-03T05:00:00,-6,50,Tunis\n2023-01-03T06:00:00,-7,48,Tunis\n2023-01-03T07:00:00,-8,46,Tunis\n2023-01-03T08:00:00,-7,48,Tunis\n2023-01-03T09:00:00,-6,50,Tunis\n2023-01-03T10:00:00,-5,52,Tunis\n2023-01-03T11:00:00,-4,54,Tunis\n2023-01-03T12:00:00,-3,56,Tunis\n2023-01-03T13:00:00,-2,58,Tunis\n2023-01-03T14:00:00,-1,60,Tunis\n2023-01-03T15:00:00,0,62,Tunis\n2023-01-03T16:00:00,1,64,Tunis\n2023-01-03T17:00:00,0,66,Tunis\n2023-01-03T18:00:00,-1,68,Tunis\n2023-01-03T19:00:00,-2,70,Tunis\n2023-01-03T20:00:00,-3,72,Tunis\n2023-01-03T21:00:00,-4,74,Tunis\n2023-01-03T22:00:00,-5,76,Tunis\n2023-01-03T23:00:00,-6,78,Tunis"


@pytest.fixture
def mock_weather_api(mocker, request):
    """Fixture to mock the weather_api call with generated data."""

    mock_client = mocker.Mock()
    mocker.patch(
        "src.data_import.weather.openmeteo_requests.Client", return_value=mock_client
    )

    def mock_weather_api_response(url, params):

        class MockVariable:
            def __init__(self, length):
                self.values = [random.randint(-10, 100) for _ in range(length)]

            def ValuesAsNumpy(self):
                return self.values

        class MockHourly:
            def __init__(self, num_var, length):
                self.var = [MockVariable(length) for _ in range(num_var)]

            def Variables(self, index):
                return self.var[index]

        class MockResponse:
            def __init__(self, params):
                self.start_date = pd.to_datetime(params.get("start_date"))
                self.end_date = pd.to_datetime(params.get("end_date")) + timedelta(
                    hours=23
                )
                self.date_range = pd.date_range(
                    start=self.start_date, end=self.end_date, freq="h"
                )
                self.latitude = params.get("latitude")
                self.longitude = params.get("longitude")
                self.timezone = params.get("timezone")
                self.h_var = params.get("hourly")

            def Hourly(self):
                return MockHourly(len(self.h_var), len(self.date_range))

        return [MockResponse(params)]

    mock_client.weather_api.side_effect = mock_weather_api_response
    return mock_client.weather_api


def test_get_weather_data_for_specific_period_mock(mock_weather_api):
    """Test that the function returns data for the specified date range."""

    city = {"name": "Tunis", "latitude": 86.819, "longitude": 10.1658}
    result = get_weather_data_city(
        city,
        start_date="2023-01-01",
        end_date="2023-01-01",
        hourly_variables=["temperature_2m", "relative_humidity_2m"],
        timezone="Africa/Tunis",
    )

    # Verify mock was called with correct parameters
    mock_weather_api.assert_called_once()

    # Validate results
    assert result is not None
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 24  # 24 hours in one day

    # Check for required columns
    assert "temperature_2m" in result.columns
    assert "relative_humidity_2m" in result.columns
    assert "date" in result.columns
