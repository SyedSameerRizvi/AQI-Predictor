"""
Open-Meteo data fetching.

It uses plain requests against the JSON endpoints rather than the FlatBuffers
client, because clarity matters more than raw speed here and the volumes are
modest. Everything is returned as a tidy pandas DataFrame indexed by a
timezone-aware UTC timestamp, with a city_id column so frames from different
cities can be stacked safely.

Two paths, because Open-Meteo splits weather across two services:
  - fetch_historical(): deep past, for backfill. Weather from the ERA5 archive
    (goes back years but lags real time by ~5 days), air quality from the air
    quality endpoint with explicit dates.

  - fetch_forecast(): recent past + future, for the live feature pipeline and
    3-day prediction. Weather from the forecast endpoint, air quality from the
    same air quality endpoint using past_days / forecast_days.

"""

import time 
from datetime import datetime, timedelta, timezone

import pandas as pd
import requests
from requests.adapters import HTTPAdapter, Retry

from src.config import (
    AIR_QUALITY_URL,
    WEATHER_ARCHIVE_URL,
    WEATHER_FORECAST_URL,
    POLLUTANTS,
    WEATHER_VARS,
)

from src.cities import City


# HTTP session with automatic retry and exponential backoff 
# API calls fail sometimes (rate limits, transient server errors). Instead of
# Crashing, It will retry with growing delays: 1s, 2s, 4s, 8s, 16s.

def _make_session() -> requests.Session:
    retry = Retry(
        total=5,
        backoff_factor=1.0,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


_SESSION = _make_session()


def _get_json(url: str, params: dict, timeout: int = 60) -> dict:
    """GET a URL and return parsed JSON, raising on any HTTP error."""
    resp = _SESSION.get(url, params=params, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def _hourly_to_df(payload: dict, variables: list[str]) -> pd.DataFrame:
    """
    Turn Open-Meteo's 'hourly' block into a DataFrame indexed by UTC time.
    We request timezone=UTC, so the returned times are already UTC; we parse
    them as tz-aware so nothing downstream can misread the zone.
    """
    hourly = payload.get("hourly")
    if not hourly or "time" not in hourly:
        return pd.DataFrame()

    df = pd.DataFrame({"time": hourly["time"]})
    for var in variables:
        df[var] = hourly.get(var)  # None -> column of NaN if a var is missing

    df["time"] = pd.to_datetime(df["time"], utc=True)
    return df.set_index("time").sort_index()


def _date_chunks(start_date: str, end_date: str, max_days: int = 120):
    """
    Yield (start, end) ISO date strings covering the range in chunks. Long
    date ranges can time out or hit request-size limits, so we split them.
    """
    start = pd.to_datetime(start_date).date()
    end = pd.to_datetime(end_date).date()
    cur = start
    while cur <= end:
        chunk_end = min(cur + timedelta(days=max_days - 1), end)
        yield cur.isoformat(), chunk_end.isoformat()
        cur = chunk_end + timedelta(days=1)


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    """Drop duplicate timestamps (keep the latest) and sort ascending."""
    return df[~df.index.duplicated(keep="last")].sort_index()


#  Historical (backfill) 

def _fetch_range(url: str, city: City, variables: list[str],
                 start_date: str, end_date: str) -> pd.DataFrame:
    """Fetch one variable set over a date range, chunked, from one endpoint."""
    frames = []
    for s, e in _date_chunks(start_date, end_date):
        params = {
            "latitude": city.lat,
            "longitude": city.lon,
            "hourly": ",".join(variables),
            "start_date": s,
            "end_date": e,
            "timezone": "UTC",
        }
        frames.append(_hourly_to_df(_get_json(url, params), variables))
    return pd.concat(frames).sort_index() if frames else pd.DataFrame()


def fetch_historical(city: City, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Deep-past pollutant + weather data for one city, merged on timestamp.
    For backfill only. Dates should end at least ~5 days before today, since
    the weather archive lags real time. Returns an empty frame if either
    source has no data for the range.
    """
    aq = _fetch_range(AIR_QUALITY_URL, city, POLLUTANTS, start_date, end_date)
    wx = _fetch_range(WEATHER_ARCHIVE_URL, city, WEATHER_VARS, start_date, end_date)
    if aq.empty or wx.empty:
        return pd.DataFrame()

    df = _clean(aq.join(wx, how="inner"))
    df.insert(0, "city_id", city.city_id)
    return df


# Forecast (recent past + future) 

def fetch_forecast(city: City, past_days: int = 7,
                   forecast_days: int = 3) -> pd.DataFrame:
    """
    Recent history plus a 3-day-ahead window for one city, merged on timestamp.
    Used by the live feature pipeline and the dashboard. past_days gives us the
    recent hours needed to build lag features; forecast_days gives the future
    weather covariates for the prediction window.
    """
    aq_params = {
        "latitude": city.lat,
        "longitude": city.lon,
        "hourly": ",".join(POLLUTANTS),
        "past_days": past_days,
        "forecast_days": forecast_days,
        "timezone": "UTC",
    }
    wx_params = {
        "latitude": city.lat,
        "longitude": city.lon,
        "hourly": ",".join(WEATHER_VARS),
        "past_days": past_days,
        "forecast_days": forecast_days,
        "timezone": "UTC",
    }
    aq = _hourly_to_df(_get_json(AIR_QUALITY_URL, aq_params), POLLUTANTS)
    wx = _hourly_to_df(_get_json(WEATHER_FORECAST_URL, wx_params), WEATHER_VARS)
    if aq.empty or wx.empty:
        return pd.DataFrame()

    df = _clean(aq.join(wx, how="inner"))
    df.insert(0, "city_id", city.city_id)
    return df


# Multiple city with per city error isolation 

def fetch_many(cities: list[City], fetch_fn, **kwargs):
    """
    Run a fetch function over many cities. One city failing must not kill the
    rest, so failures are collected, not raised. Returns (results, failures):
      results  -> {city_id: DataFrame}
      failures -> {city_id: reason}
    """
    results, failures = {}, {}
    for city in cities:
        try:
            df = fetch_fn(city, **kwargs)
            if df.empty:
                failures[city.city_id] = "empty response"
            else:
                results[city.city_id] = df
        except Exception as exc:  # noqa: BLE001 - we want to catch everything here
            failures[city.city_id] = str(exc)
        time.sleep(0.5)  # be polite to the API between cities
    return results, failures


# CLI sanity check 

if __name__ == "__main__":
    from src.cities import get_city
    from src.aqi import add_aqi_columns

    city = get_city("pk-karachi")
    # end 8 days ago so the weather archive definitely has the data
    end = datetime.now(timezone.utc).date() - timedelta(days=8)
    start = end - timedelta(days=7)

    print(f"Fetching {city.name} history {start} -> {end} ...")
    raw = fetch_historical(city, start.isoformat(), end.isoformat())
    print(f"rows returned: {len(raw)}")

    if not raw.empty:
        with_aqi = add_aqi_columns(raw)
        cols = ["pm2_5", "pm10", "ozone", "aqi", "aqi_dominant"]
        print(with_aqi[cols].tail(10).to_string())
        print("\nsanity: pm2_5 should be tens-to-hundreds ug/m3,")
        print("aqi_dominant is almost always pm2_5 in Karachi.")
    else:
        print("empty frame: check the date range and your connection.")