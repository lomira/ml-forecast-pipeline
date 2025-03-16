import pytest
import pandas as pd
import random
from datetime import datetime
from src.data_import.weather import (
    get_weather_data_city,
    setup_openmeteo_client,
    load_existing_data,
)


# Data from "2023-01-02T00:00" to "2023-01-03T23:00" for mocking purposes
CSV_DATA = "date,temperature_2m,relative_humidity_2m,city\n2023-01-02T00:00:00,5,80,Tunis\n2023-01-02T01:00:00,4,82,Tunis\n2023-01-02T02:00:00,3,84,Tunis\n2023-01-02T03:00:00,2,86,Tunis\n2023-01-02T04:00:00,1,88,Tunis\n2023-01-02T05:00:00,0,90,Tunis\n2023-01-02T06:00:00,-1,92,Tunis\n2023-01-02T07:00:00,-2,94,Tunis\n2023-01-02T08:00:00,-1,92,Tunis\n2023-01-02T09:00:00,0,90,Tunis\n2023-01-02T10:00:00,1,88,Tunis\n2023-01-02T11:00:00,2,86,Tunis\n2023-01-02T12:00:00,3,84,Tunis\n2023-01-02T13:00:00,4,82,Tunis\n2023-01-02T14:00:00,5,80,Tunis\n2023-01-02T15:00:00,6,78,Tunis\n2023-01-02T16:00:00,7,76,Tunis\n2023-01-02T17:00:00,6,74,Tunis\n2023-01-02T18:00:00,5,72,Tunis\n2023-01-02T19:00:00,4,70,Tunis\n2023-01-02T20:00:00,3,68,Tunis\n2023-01-02T21:00:00,2,66,Tunis\n2023-01-02T22:00:00,1,64,Tunis\n2023-01-02T23:00:00,0,62,Tunis\n2023-01-03T00:00:00,-1,60,Tunis\n2023-01-03T01:00:00,-2,58,Tunis\n2023-01-03T02:00:00,-3,56,Tunis\n2023-01-03T03:00:00,-4,54,Tunis\n2023-01-03T04:00:00,-5,52,Tunis\n2023-01-03T05:00:00,-6,50,Tunis\n2023-01-03T06:00:00,-7,48,Tunis\n2023-01-03T07:00:00,-8,46,Tunis\n2023-01-03T08:00:00,-7,48,Tunis\n2023-01-03T09:00:00,-6,50,Tunis\n2023-01-03T10:00:00,-5,52,Tunis\n2023-01-03T11:00:00,-4,54,Tunis\n2023-01-03T12:00:00,-3,56,Tunis\n2023-01-03T13:00:00,-2,58,Tunis\n2023-01-03T14:00:00,-1,60,Tunis\n2023-01-03T15:00:00,0,62,Tunis\n2023-01-03T16:00:00,1,64,Tunis\n2023-01-03T17:00:00,0,66,Tunis\n2023-01-03T18:00:00,-1,68,Tunis\n2023-01-03T19:00:00,-2,70,Tunis\n2023-01-03T20:00:00,-3,72,Tunis\n2023-01-03T21:00:00,-4,74,Tunis\n2023-01-03T22:00:00,-5,76,Tunis\n2023-01-03T23:00:00,-6,78,Tunis"


def filter_api_data(api_data: dict, start_date: str, end_date: str):
    start_datetime = datetime.fromisoformat(start_date)
    end_datetime = datetime.fromisoformat(end_date)

    filtered_time = []
    filtered_temp = []
    filtered_humidity = []

    for i, time_str in enumerate(api_data["hourly"]["time"]):
        current_datetime = datetime.fromisoformat(time_str)
        if start_datetime <= current_datetime <= end_datetime:
            filtered_time.append(time_str)
            filtered_temp.append(api_data["hourly"]["temperature_2m"][i])
            filtered_humidity.append(api_data["hourly"]["relative_humidity_2m"][i])

    filtered_data = api_data.copy()
    filtered_data["hourly"]["time"] = filtered_time
    filtered_data["hourly"]["temperature_2m"] = filtered_temp
    filtered_data["hourly"]["relative_humidity_2m"] = filtered_humidity

    return filtered_data


@pytest.fixture
def mock_weather_api(mocker):
    """Fixture to mock the weather_api call with generated data."""
    # Patch the client creation first
    mock_client = mocker.Mock()
    mocker.patch(
        "src.data_import.weather.openmeteo_requests.Client", return_value=mock_client
    )

    def mock_weather_api_response(url, params=None):
        # Extract parameters
        start_date = params.get("start_date")
        end_date = params.get("end_date")
        latitude = params.get("latitude", 52.52)
        longitude = params.get("longitude", 13.419998)
        timezone = params.get("timezone", "Europe/Berlin")

        # Generate time range
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        date_range = pd.date_range(start=start, end=end, freq="h")
        time_strings = [d.strftime("%Y-%m-%dT%H:%M") for d in date_range]

        # Generate random temperature and humidity data
        temp_data = [
            round(random.uniform(5.0, 25.0), 1) for _ in range(len(time_strings))
        ]
        humidity_data = [random.randint(50, 95) for _ in range(len(time_strings))]

        # Create response structure
        mock_data = {
            "latitude": latitude,
            "longitude": longitude,
            "timezone": timezone,
            "timezone_abbreviation": "GMT+1",
            "hourly_units": {
                "time": "iso8601",
                "temperature_2m": "°C",
                "relative_humidity_2m": "%",
            },
            "hourly": {
                "time": time_strings,
                "temperature_2m": temp_data,
                "relative_humidity_2m": humidity_data,
            },
        }

        return mock_data

    mock_client.weather_api.side_effect = mock_weather_api_response
    return mock_client.weather_api


def test_get_weather_data_for_specific_period(mock_weather_api):
    """Test that the function returns data for the specified date range."""
    # Test city
    city = {"name": "Tunis", "latitude": 86.819, "longitude": 10.1658}

    # Specific date range with manageable number of days
    start_date = "2023-01-01"
    end_date = "2023-01-01"  # Just one day = 24 hours

    # Call function with parameters
    result = get_weather_data_city(
        city,
        start_date=start_date,
        end_date=end_date,
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
    assert "time" in result.columns
