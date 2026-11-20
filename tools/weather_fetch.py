"""Fetch hourly historical weather for a site from Open-Meteo and save it as CSV.

Usage in a Jupyter notebook:
    from weather_fetch import fetch_weather

    df = fetch_weather(55.5, 8.9, "glejbjerg")   # writes weather_glejbjerg.csv
    sites = {"glejbjerg": (55.5, 8.9), "onshore_site": (56.0, 9.0)}
    for name, (lat, lon) in sites.items():
        fetch_weather(lat, lon, name)

Requires: openmeteo-requests, requests-cache, retry-requests, pandas
"""
from pathlib import Path

import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry

URL = "https://archive-api.open-meteo.com/v1/archive"

HOURLY_VARIABLES = [
    "temperature_2m",
    "relative_humidity_2m",
    "wind_speed_10m",
    "wind_speed_100m",
    "wind_direction_10m",
    "wind_direction_100m",
    "surface_pressure",
    "shortwave_radiation",
    "direct_normal_irradiance",
    "diffuse_radiation",
]

# Open-Meteo client with cache and retry on error
_cache_session = requests_cache.CachedSession(".cache", expire_after=-1)
_retry_session = retry(_cache_session, retries=5, backoff_factor=0.2)
_client = openmeteo_requests.Client(session=_retry_session)


def fetch_weather(
    lat: float,
    lon: float,
    name: str,
    start_date: str = "2025-01-01",
    end_date: str = "2025-12-31",
    model: str | None = "era5",
    variables: list[str] = HOURLY_VARIABLES,
    outdir: str = ".",
) -> pd.DataFrame:
    """Fetch hourly weather for (lat, lon), save to weather_{name}.csv, return the DataFrame.

    Timestamps are UTC. Wind speed is in m/s, pressure in hPa, temperature in degC.
    Radiation columns are the mean of the preceding hour (W/m2).
    Set model=None to use Open-Meteo's default model selection.
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": list(variables),
        "timezone": "auto",
        "wind_speed_unit": "ms",
    }
    if model:
        params["models"] = model

    response = _client.weather_api(URL, params=params)[0]
    hourly = response.Hourly()

    data = {
        "date": pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left",
        )
    }
    # Order must match the order requested in `variables`
    for i, var in enumerate(variables):
        data[var] = hourly.Variables(i).ValuesAsNumpy()

    df = pd.DataFrame(data)

    safe_name = str(name).strip().replace(" ", "_").replace("/", "_")
    path = Path(outdir) / f"weather_{safe_name}.csv"
    df.to_csv(path, index=False)

    print(
        f"{name}: {response.Latitude():.3f}N {response.Longitude():.3f}E, "
        f"elevation {response.Elevation():.0f} m, {len(df)} rows -> {path}"
    )
    return df


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 4:
        sys.exit("usage: python weather_fetch.py LAT LON NAME")
    fetch_weather(float(sys.argv[1]), float(sys.argv[2]), sys.argv[3])
