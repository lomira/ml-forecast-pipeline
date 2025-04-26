import pandas as pd
from src.data_import.weather import get_weather_data_city
from .utils import mock_openmeteo_client


# Test with out existing data
def test_get_weather_single_day_no_existing_data(
    mock_openmeteo_client, mocker
):  # Add mocker
    # Mock load_existing_data to ensure no data is loaded
    mocker.patch("src.data_import.weather.load_existing_data", return_value=None)
    # Mock save to avoid actual file writing during test
    mocker.patch("src.data_import.weather.pd.DataFrame.to_csv")

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


def test_get_weather_single_week_no_existing_data(mock_openmeteo_client, mocker):
    # Mock load_existing_data to ensure no data is loaded
    mocker.patch("src.data_import.weather.load_existing_data", return_value=None)
    # Mock save to avoid actual file writing during test
    mocker.patch("src.data_import.weather.pd.DataFrame.to_csv")

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
    assert len(result) == 24 * 7  # Should have 24 hours * 7 days


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
    # Mock save to avoid actual file writing during test
    mocker.patch("src.data_import.weather.pd.DataFrame.to_csv")

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
    # Mock save to avoid actual file writing during test
    mocker.patch("src.data_import.weather.pd.DataFrame.to_csv")

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
    # Mock save to avoid actual file writing during test
    mocker.patch("src.data_import.weather.pd.DataFrame.to_csv")

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
    # Mock save to avoid actual file writing during test
    mocker.patch("src.data_import.weather.pd.DataFrame.to_csv")

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
    # Mock save to avoid actual file writing during test
    mocker.patch("src.data_import.weather.pd.DataFrame.to_csv")

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


def test_get_weather_missing_columns_existing_dates(mock_openmeteo_client, mocker):
    """Test fetching data when dates exist but columns are missing."""
    city = {"name": "Tunis", "latitude": 86.819, "longitude": 10.1658}
    requested_hourly_variables = ["temperature_2m", "relative_humidity_2m"]

    start_date = "2023-01-01"
    end_date = "2023-01-03"

    existing_dates = pd.date_range(start=start_date, end=end_date, freq="h")
    existing_data = pd.DataFrame(
        {
            "date": existing_dates,
            "temperature_2m": [20] * len(existing_dates),
            # Missing "relative_humidity_2m"
            "city": city["name"],
        }
    )

    # Mock load_existing_data to return the incomplete data
    mocker.patch(
        "src.data_import.weather.load_existing_data", return_value=existing_data
    )
    # Mock save to avoid actual file writing during test
    mocker.patch("src.data_import.weather.pd.DataFrame.to_csv")

    result = get_weather_data_city(
        city,
        start_date=start_date,
        end_date=end_date,
        hourly_variables=requested_hourly_variables,
        timezone="Africa/Tunis",
    )

    # Assert API was called because columns were missing
    assert mock_openmeteo_client.last_call is not None

    # Assert the API call was for the *full* date range, despite dates existing
    call_params = mock_openmeteo_client.last_call["params"]
    assert call_params["start_date"] == start_date
    assert call_params["end_date"] == end_date
    assert call_params["hourly"] == requested_hourly_variables

    # Assert the result contains all requested columns and the correct date range
    assert isinstance(result, pd.DataFrame)
    assert "city" in result.columns
    assert result["city"].iloc[0] == "Tunis"
    for var in requested_hourly_variables:
        assert var in result.columns
    # Calculate expected hours for the full date range (inclusive)
    num_days = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days + 1
    expected_hours = num_days * 24
    assert len(result) == expected_hours  # Should cover the full original range
    assert result["date"].min() == pd.Timestamp(start_date)
    # Check end date considering the hourly frequency includes the last day up to 23:00
    expected_end_datetime = pd.Timestamp(end_date) + pd.Timedelta(hours=23)
    assert result["date"].max() == expected_end_datetime
