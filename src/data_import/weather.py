import openmeteo_requests
import requests_cache
import pandas as pd
import os
from retry_requests import retry
from typing import List, Tuple, Union
from datetime import timedelta
from pandas.errors import EmptyDataError, ParserError  # Import specific pandas errors


def setup_openmeteo_client():
    """Setup the Open-Meteo API client with cache and retry on error."""
    cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    return openmeteo_requests.Client(session=retry_session)


def get_file_path(city_name) -> str:
    """Generate a standardized filename for storing weather data."""
    data_dir = os.path.join("data", "weather")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(
        data_dir,
        f"{city_name.lower().replace(' ', '_')}.csv",
    )


def get_missing_date_ranges(
    available_start,
    available_end,
    requested_start,
    requested_end,
) -> List[Tuple[str, str]]:
    """Determine which date ranges need to be fetched from the API."""
    missing_ranges = []

    # Convert strings to datetime to perfect difference
    available_start = pd.to_datetime(available_start)
    available_end = pd.to_datetime(available_end)
    requested_start = pd.to_datetime(requested_start)
    requested_end = pd.to_datetime(requested_end)

    # Validate date ranges
    if available_start > available_end:
        raise ValueError("Available start date cannot be after available end date.")

    if requested_start > requested_end:
        raise ValueError("Requested start date cannot be after requested end date.")

    # Case 1: Request weather data before available data
    if requested_start < available_start:
        missing_ranges.append((requested_start, available_start - timedelta(days=1)))

    # Case 2: Request weather data after available data
    if requested_end > available_end:
        missing_ranges.append((available_end + timedelta(days=1), requested_end))

    # Convert back to string format for API
    return [
        (r[0].strftime("%Y-%m-%d"), r[1].strftime("%Y-%m-%d")) for r in missing_ranges
    ]


def get_dates_to_fetch(
    city_weather: Union[pd.DataFrame, None],
    start_date: str,
    end_date: str,
) -> List[Tuple[str, str]]:
    """Determine which date ranges need to be fetched from the API based on current data"""

    # If the city does not exist, we need to fetch the entire range
    if city_weather is None:
        return [(start_date, end_date)]

    requested_start = pd.to_datetime(start_date)
    requested_end = pd.to_datetime(end_date)
    available_start = city_weather["date"].min()
    available_end = city_weather["date"].max()
    return get_missing_date_ranges(
        available_start, available_end, requested_start, requested_end
    )


def fetch_weather_city_from_api(
    city: dict,
    date_range: List[str],
    hourly_variables: List[str],
    timezone: str,
):
    """Fetch weather data from Open-Meteo API."""
    openmeteo = setup_openmeteo_client()
    url = "https://historical-forecast-api.open-meteo.com/v1/forecast"
    params = {
        "latitude": city["latitude"],
        "longitude": city["longitude"],
        "start_date": date_range[0],
        "end_date": date_range[1],
        "hourly": hourly_variables,
        "timezone": timezone,
    }

    # Get weather data from the API
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]
    hourly = response.Hourly()

    # Initialize data dictionary with dates
    range_start = pd.to_datetime(date_range[0])
    # Add 23 hours as range is in days and we need until 23:00
    range_end = pd.to_datetime(date_range[1]) + timedelta(hours=23)
    # hourly_data = {"date": date_range.tz_convert(timezone)}
    date_range_all = pd.date_range(start=range_start, end=range_end, freq="h")
    hourly_data = {"date": date_range_all}

    # Parse the response
    for j, variable in enumerate(hourly_variables):
        hourly_data[variable] = hourly.Variables(j).ValuesAsNumpy()

    # Add metadata
    hourly_data["city"] = city["name"]
    # Create DataFrame
    return pd.DataFrame(data=hourly_data)


def load_existing_data(city) -> Union[pd.DataFrame, None]:
    """
    Check if we already have data for this city.
    Returns the data if available, otherwise None.
    Handles potential file read errors.
    """
    filepath = get_file_path(city["name"])

    if os.path.exists(filepath):
        try:
            print(f"Loading data for {city['name']} from {filepath}")
            df = pd.read_csv(filepath, parse_dates=["date"])
            # Check if dataframe is empty after loading
            if df.empty:
                print(f"Warning: File {filepath} is empty.")
                return None
            return df
        except (EmptyDataError, ParserError) as e:
            print(f"Error reading {filepath}: {e}. Treating as no existing data.")
            return None
        except Exception as e:  # Catch other potential read errors
            print(
                f"Unexpected error reading {filepath}: {e}. Treating as no existing data."
            )
            return None
    else:
        return None


def get_weather_data_city(
    city: dict,
    start_date: str,
    end_date: str,
    hourly_variables: List[str],
    timezone: str,
) -> pd.DataFrame:
    """
    Get historical weather data, using local storage when available and fetching from API only when needed.

    Args:
        city: Dictionaries, each with 'name', 'latitude', and 'longitude'
        start_date: Start date in 'YYYY-MM-DD' format,
        end_date: End date in 'YYYY-MM-DD' format)
        hourly_variables: List of hourly weather variables to fetch
        timezone: Timezone for the data

    Returns:
        Dictionary mapping city names to pandas DataFrames with weather data
    """

    # Check for existing data for each city
    existing_data = load_existing_data(city)
    fetching_dates = get_dates_to_fetch(existing_data, start_date, end_date)

    if not fetching_dates:
        # No new dates to fetch based on date range alone
        # Check if all requested variables (columns) are present in the existing data
        if existing_data is not None:
            missing_columns = [
                col for col in hourly_variables if col not in existing_data.columns
            ]
            if not missing_columns:
                # All dates and columns are present
                print(
                    f"Data for {city['name']} ({start_date} to {end_date}) with requested columns already available locally."
                )
                return existing_data
            else:
                # Dates are covered, but columns are missing. Re-fetch the entire range.
                print(
                    f"Missing columns {missing_columns} in existing data for {city['name']}. Re-fetching full range {start_date} to {end_date}."
                )
                fetching_dates = [(start_date, end_date)]
                # Discard incomplete existing data as we are re-fetching everything
                existing_data = None
        else:
            # This case implies load_existing_data returned None, and get_dates_to_fetch
            # might have returned an empty list if start/end dates were within a non-existent range (shouldn't happen with current logic but handle defensively).
            # If existing_data is None, we must fetch the full range.
            fetching_dates = [(start_date, end_date)]

    # If we reach here, either fetching_dates was initially non-empty (missing dates),
    # or it was set because columns were missing or existing_data was None.

    # Fetch data for each required date range
    all_new_data = []  # Collect new data chunks here
    print(f"Fetching data for {city['name']} for date ranges: {fetching_dates}")
    for date_range in fetching_dates:
        new_data_chunk = fetch_weather_city_from_api(
            city, date_range, hourly_variables, timezone
        )
        all_new_data.append(new_data_chunk)

    # Combine potentially existing data (if columns were initially okay but dates were missing)
    # with all newly fetched data.
    # If columns were missing, existing_data was set to None earlier.
    if not all_new_data:
        # This should only happen if fetching_dates was empty and existing_data was sufficient
        # which is handled by the return statement earlier. Added for safety.
        final_data = existing_data
    else:
        final_data = pd.concat([existing_data] + all_new_data, ignore_index=True)

        # Sort and remove potential duplicates introduced by concatenation or overlap
        final_data = final_data.sort_values("date").drop_duplicates(
            subset=["date"], keep="last"
        )

        # Save the updated/combined data back to the file
        filepath = get_file_path(city["name"])
        try:
            final_data.to_csv(filepath, index=False)
            print(f"Saved updated data for {city['name']} to {filepath}")
        except Exception as e:
            print(f"Error saving data for {city['name']} to {filepath}: {e}")

    return final_data


# Juste to test the function
# TODO : Remove this part after testing
if __name__ == "__main__":
    cities = [
        {"name": "Tunis", "latitude": 36.819, "longitude": 10.1658},
        {"name": "Sfax", "latitude": 34.7406, "longitude": 10.7600},
    ]

    hourly_vars = ["temperature_2m", "relative_humidity_2m", "precipitation"]

    weather_data = get_weather_data_city(
        city=cities[0],
        start_date="2024-01-01",
        end_date="2024-01-07",
        hourly_variables=hourly_vars,
        timezone="Africa/Tunis",
    )
    print(weather_data.head())
