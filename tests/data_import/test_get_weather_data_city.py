import re
import pandas as pd
from tests.data_import.utils import mock_openmeteo_client
from src.data_import.weather import get_weather_data_city


# Test with out existing data
def test_get_weather_single_day_no_existing_data(mock_openmeteo_client):
    city = {"name": "Tunis", "latitude": 86.819, "longitude": 10.1658}
    hourly_variables = ["temperature_2m", "relative_humidity_2m"]
    result = get_weather_data_city(
        city,
        start_date="2023-01-01",
        end_date="2023-01-01",
        hourly_variables=hourly_variables,
        timezone="Africa/Tunis",
    )

    assert mock_openmeteo_client.last_call is not None
    assert isinstance(result, pd.DataFrame)
    assert "city" in result.columns
    assert result["city"].iloc[0] == "Tunis"
    assert "temperature_2m" in result.columns
    assert len(result) == 24  # Should have 24 hours for a single day


def test_get_weather_single_week_no_existing_data(mock_openmeteo_client):
    city = {"name": "Tunis", "latitude": 86.819, "longitude": 10.1658}
    hourly_variables = ["temperature_2m", "relative_humidity_2m"]
    result = get_weather_data_city(
        city,
        start_date="2022-01-01",
        end_date="2022-01-07",
        hourly_variables=hourly_variables,
        timezone="Africa/Tunis",
    )

    # Verify the result is a DataFrame with expected properties
    assert isinstance(result, pd.DataFrame)
    assert "city" in result.columns
    assert result["city"].iloc[0] == "Tunis"

    # Check all variables are in the result
    for variable in hourly_variables:
        assert variable in result.columns

    # Verify the API was called
    assert mock_openmeteo_client.last_call is not None
    assert isinstance(result, pd.DataFrame)
    assert "city" in result.columns
    assert result["city"].iloc[0] == "Tunis"
    assert "temperature_2m" in result.columns
    assert len(result) == 24 * 7  # Should have 24 hours for a single day


# Test with existing data
def test_get_weather_extensive_existing_data(mock_openmeteo_client, mocker):
    city = {"name": "Tunis", "latitude": 86.819, "longitude": 10.1658}
    hourly_variables = ["temperature_2m", "relative_humidity_2m"]

    existing_dates = pd.date_range(start="2023-01-01", end="2023-01-03", freq="h")
    existing_data = pd.DataFrame(
        {
            "date": existing_dates,
            "temperature_2m": [20] * len(existing_dates),
            "relative_humidity_2m": [50] * len(existing_dates),
            "city": city["name"],
        }
    )

    # Mock load_existing_data to return our existing data
    mocker.patch(
        "src.data_import.weather.load_existing_data", return_value=existing_data
    )

    result = get_weather_data_city(
        city,
        start_date="2023-01-01",
        end_date="2023-01-01",
        hourly_variables=hourly_variables,
        timezone="Africa/Tunis",
    )

    assert mock_openmeteo_client.last_call is None
    assert isinstance(result, pd.DataFrame)
    assert "city" in result.columns
    assert result["city"].iloc[0] == "Tunis"
    assert "temperature_2m" in result.columns
    assert len(result) == len(existing_dates)  # Should have the same as the database


def test_get_weather_exact_existing_data(mock_openmeteo_client, mocker):
    city = {"name": "Tunis", "latitude": 86.819, "longitude": 10.1658}
    hourly_variables = ["temperature_2m", "relative_humidity_2m"]

    existing_dates = pd.date_range(start="2023-01-01", end="2023-01-03", freq="h")
    existing_data = pd.DataFrame(
        {
            "date": existing_dates,
            "temperature_2m": [20] * len(existing_dates),
            "relative_humidity_2m": [50] * len(existing_dates),
            "city": city["name"],
        }
    )

    # Mock load_existing_data to return our existing data
    mocker.patch(
        "src.data_import.weather.load_existing_data", return_value=existing_data
    )

    result = get_weather_data_city(
        city,
        start_date="2023-01-01",
        end_date="2023-01-03",
        hourly_variables=hourly_variables,
        timezone="Africa/Tunis",
    )

    assert mock_openmeteo_client.last_call is None
    assert isinstance(result, pd.DataFrame)
    assert "city" in result.columns
    assert result["city"].iloc[0] == "Tunis"
    assert "temperature_2m" in result.columns
    assert len(result) == len(existing_dates)  # Should have the same as the database


def test_get_weather_partial_same_start_existing_data(mock_openmeteo_client, mocker):
    city = {"name": "Tunis", "latitude": 86.819, "longitude": 10.1658}
    hourly_variables = ["temperature_2m", "relative_humidity_2m"]

    existing_date_start = "2023-01-01"
    existing_dates_end = "2023-01-03"
    existing_dates = pd.date_range(
        start=existing_date_start, end=existing_dates_end, freq="h"
    )
    existing_data = pd.DataFrame(
        {
            "date": existing_dates,
            "temperature_2m": [20] * len(existing_dates),
            "relative_humidity_2m": [50] * len(existing_dates),
            "city": city["name"],
        }
    )

    # Mock load_existing_data to return our existing data
    mocker.patch(
        "src.data_import.weather.load_existing_data", return_value=existing_data
    )

    query_start_date = "2023-01-01"
    query_end_date = "2023-01-07"
    query_range = pd.date_range(start=query_start_date, end=query_end_date, freq="h")

    result = get_weather_data_city(
        city,
        start_date=query_start_date,
        end_date=query_end_date,
        hourly_variables=hourly_variables,
        timezone="Africa/Tunis",
    )

    # API Call
    assert mock_openmeteo_client.last_call is not None
    call_params = mock_openmeteo_client.last_call["params"]
    assert call_params["start_date"] == "2023-01-04"
    assert call_params["end_date"] == max(existing_dates_end, query_end_date)

    # Result
    assert isinstance(result, pd.DataFrame)
    assert "city" in result.columns
    assert result["city"].iloc[0] == "Tunis"
    assert "temperature_2m" in result.columns
    assert len(result) == len(query_range)  # Should have the same as the api return


def test_get_weather_partial_same_end_existing_data(mock_openmeteo_client, mocker):
    city = {"name": "Tunis", "latitude": 86.819, "longitude": 10.1658}
    hourly_variables = ["temperature_2m", "relative_humidity_2m"]

    existing_dates = pd.date_range(start="2023-01-03", end="2023-01-07", freq="h")
    existing_data = pd.DataFrame(
        {
            "date": existing_dates,
            "temperature_2m": [20] * len(existing_dates),
            "relative_humidity_2m": [50] * len(existing_dates),
            "city": city["name"],
        }
    )

    # Mock load_existing_data to return our existing data
    mocker.patch(
        "src.data_import.weather.load_existing_data", return_value=existing_data
    )

    query_start_date = "2023-01-01"
    query_end_date = "2023-01-07"
    query_range = pd.date_range(start=query_start_date, end=query_end_date, freq="h")

    result = get_weather_data_city(
        city,
        start_date=query_start_date,
        end_date=query_end_date,
        hourly_variables=hourly_variables,
        timezone="Africa/Tunis",
    )

    # API Call
    assert mock_openmeteo_client.last_call is not None
    call_params = mock_openmeteo_client.last_call["params"]
    assert call_params["start_date"] == "2023-01-01"
    assert call_params["end_date"] == "2023-01-02"

    # Results
    assert isinstance(result, pd.DataFrame)
    assert "city" in result.columns
    assert result["city"].iloc[0] == "Tunis"
    assert "temperature_2m" in result.columns
    assert len(result) == len(query_range)  # Should have the same as the api return


def test_get_weather_partial_before_after_existing_data(mock_openmeteo_client, mocker):
    city = {"name": "Tunis", "latitude": 86.819, "longitude": 10.1658}
    hourly_variables = ["temperature_2m", "relative_humidity_2m"]

    existing_dates = pd.date_range(start="2023-01-03", end="2023-01-05", freq="h")
    existing_data = pd.DataFrame(
        {
            "date": existing_dates,
            "temperature_2m": [20] * len(existing_dates),
            "relative_humidity_2m": [50] * len(existing_dates),
            "city": city["name"],
        }
    )

    # Mock load_existing_data to return our existing data
    mocker.patch(
        "src.data_import.weather.load_existing_data", return_value=existing_data
    )

    query_start_date = "2023-01-01"
    query_end_date = "2023-01-07"
    query_range = pd.date_range(start=query_start_date, end=query_end_date, freq="h")

    result = get_weather_data_city(
        city,
        start_date=query_start_date,
        end_date=query_end_date,
        hourly_variables=hourly_variables,
        timezone="Africa/Tunis",
    )

    # API Call
    assert mock_openmeteo_client.last_call is not None
    first_call_params = mock_openmeteo_client.first_call["params"]
    assert first_call_params["start_date"] == "2023-01-01"
    assert first_call_params["end_date"] == "2023-01-02"

    last_call_params = mock_openmeteo_client.last_call["params"]
    assert last_call_params["start_date"] == "2023-01-06"
    assert last_call_params["end_date"] == "2023-01-07"

    # Results
    assert isinstance(result, pd.DataFrame)
    assert "city" in result.columns
    assert result["city"].iloc[0] == "Tunis"
    assert "temperature_2m" in result.columns
    assert len(result) == len(query_range)
