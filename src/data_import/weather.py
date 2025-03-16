import openmeteo_requests
import requests_cache
import pandas as pd
import os
from retry_requests import retry
from typing import List, Tuple, Union
from datetime import datetime, timedelta


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


def load_existing_data(city) -> Union[pd.DataFrame, None]:
    """
    Check if we already have data for this city.
    Returns the data if available, otherwise None.
    """
    filepath = get_file_path(city["name"])

    if os.path.exists(filepath):
        print(f"Loading data for {city['name']} from {filepath}")
        return pd.read_csv(filepath, parse_dates=["date"])
    else:
        return None


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


## Following code is WIP basically copy pasted from Open Meteo Docs
def fetch_weather_data(cities, start_date, end_date, hourly_variables, timezone):
    """Fetch weather data from Open-Meteo API."""
    openmeteo = setup_openmeteo_client()

    # Extract coordinates
    latitudes = [city["latitude"] for city in cities]
    longitudes = [city["longitude"] for city in cities]

    # Prepare API request
    url = "https://historical-forecast-api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitudes,
        "longitude": longitudes,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": hourly_variables,
        "timezone": timezone,
    }

    # Make API request
    responses = openmeteo.weather_api(url, params=params)

    # Process responses
    results = {}

    for i, response in enumerate(responses):
        city_name = cities[i]["name"]
        hourly = response.Hourly()

        # Create date range
        date_range = pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left",
        )

        # Convert to specified timezone if not 'auto'
        if timezone != "auto":
            date_range = date_range.tz_convert(timezone)

        # Initialize data dictionary with dates
        hourly_data = {"date": date_range}

        # Add all requested variables
        for j, variable in enumerate(hourly_variables):
            hourly_data[variable] = hourly.Variables(j).ValuesAsNumpy()

        # Add metadata
        hourly_data["city"] = city_name
        hourly_data["latitude"] = response.Latitude()
        hourly_data["longitude"] = response.Longitude()

        # Create DataFrame
        df = pd.DataFrame(data=hourly_data)
        results[city_name] = df

        # Save to file
        save_path = get_file_path(city_name, start_date, end_date)
        df.to_csv(save_path, index=False)
        print(f"Saved new data for {city_name} to {save_path}")

    return results


def get_weather_data(
    cities, start_date, end_date, hourly_variables=["temperature_2m"], timezone="auto"
):
    """
    Get historical weather data, using local storage when available and fetching from API only when needed.

    Args:
        cities: List of dictionaries, each with 'name', 'latitude', and 'longitude'
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
        hourly_variables: List of hourly weather variables to fetch
        timezone: Timezone for the data

    Returns:
        Dictionary mapping city names to pandas DataFrames with weather data
    """
    results = {}
    cities_to_fetch = []

    # Check for existing data for each city
    for city in cities:
        existing_data = load_existing_data(city, start_date, end_date)

        if existing_data is not None:
            # Check if we have all requested variables
            missing_variables = [
                var for var in hourly_variables if var not in existing_data.columns
            ]

            # Check if date range is complete
            date_range = pd.date_range(start=start_date, end=end_date, freq="H")
            has_complete_dates = len(date_range) == len(existing_data)

            if not missing_variables and has_complete_dates:
                print(f"Using existing data for {city['name']}")
                results[city["name"]] = existing_data
            else:
                print(
                    f"Existing data for {city['name']} is incomplete or missing variables {missing_variables}"
                )
                cities_to_fetch.append(city)
        else:
            print(f"No existing data found for {city['name']}")
            cities_to_fetch.append(city)

    # Fetch data for cities that need it
    if cities_to_fetch:
        print(f"Fetching data for {len(cities_to_fetch)} cities from API")
        new_data = fetch_weather_data(
            cities_to_fetch, start_date, end_date, hourly_variables, timezone
        )
        results.update(new_data)

    return results


# Juste to test the function
# TODO : Remove this part after testing
if __name__ == "__main__":
    cities = [
        {"name": "Tunis", "latitude": 36.819, "longitude": 10.1658},
        {"name": "Sfax", "latitude": 34.7406, "longitude": 10.7600},
    ]

    hourly_vars = ["temperature_2m", "relative_humidity_2m", "precipitation"]

    weather_data = get_weather_data(
        cities=cities,
        start_date="2024-01-01",
        end_date="2024-01-07",
        hourly_variables=hourly_vars,
        timezone="Africa/Tunis",
    )
