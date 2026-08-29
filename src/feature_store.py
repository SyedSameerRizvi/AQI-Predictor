"""
Hopsworks feature store access: connect, write, read.

Timestamps live on the DataFrame index everywhere else in the codebase, but
Hopsworks needs the primary key and event time as columns, so reset the
index and expose a tz-naive UTC `timestamp` column before writing.

Primary key is composite: (city_id, timestamp). This is what lets hourly runs
upsert a city's rows without touching another city's, and lets recent rows get
their targets filled in later once the future data exists.
"""

import os

import pandas as pd
from dotenv import load_dotenv

from src.config import (
    FEATURE_GROUP_NAME,
    FEATURE_GROUP_VERSION,
)

load_dotenv()
from hsfs.statistics_config import StatisticsConfig



# cached across calls so it is logged in once per process
_project = None
_fs = None
_fg = None


def the_connect():
    """this is to log in to Hopsworks and cache the project + feature store handles."""
    global _project, _fs
    if _fs is not None:
        return _fs
    import hopsworks
    _project = hopsworks.login(
        project=os.environ.get("HOPSWORKS_PROJECT"),
        api_key_value=os.environ["HOPSWORKS_API_KEY"],
    )
    _fs = _project.get_feature_store()
    return _fs


def get_feature_group():
    """this function returns the feature group, creating it on first use."""
    global _fg
    if _fg is not None:
        return _fg
    fs = the_connect()
    _fg = fs.get_or_create_feature_group(
        name=FEATURE_GROUP_NAME,
        version=FEATURE_GROUP_VERSION,
        description="Hourly AQI features and targets, one row per city per hour",
        primary_key=["city_id", "timestamp"],
        event_time="timestamp",
        online_enabled=True,
        time_travel_format="HUDI",
        stream=True,
        statistics_config=StatisticsConfig(enabled=False),
    )
    return _fg


def _prepare(df: pd.DataFrame) -> pd.DataFrame:
    """
    This function moves the UTC index into a tz-naive `timestamp` column so Hopsworks can use
    it as event time and part of the primary key.
    """
    out = df.copy()
    ts = out.index
    if ts.tz is not None:
        ts = ts.tz_convert("UTC").tz_localize(None)
    out.insert(0, "timestamp", ts)
    out = out.reset_index(drop=True)
    return out


def insert_features(df: pd.DataFrame):
    """
    Upsert a feature DataFrame (UTC index, city_id column) into the store.
    The first insert defines the schema and kicks off a background job that can
    take a few minutes, which is expected.
    """
    if df.empty:
        print("insert_features: empty frame, nothing to write")
        return
    fg = get_feature_group()
    fg.insert(_prepare(df), write_options={"wait_for_job": False})


def read_all(city_ids: list[str] | None = None) -> pd.DataFrame:
    """
    Read the feature group from the online store (RonDB), which is reliable on
    the free tier. The offline/Arrow Flight path is avoided because it is
    unstable there. Restores the UTC DatetimeIndex.
    """
    fg = get_feature_group()
    df = fg.read(online=True)
    if city_ids is not None:
        df = df[df["city_id"].isin(city_ids)]
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return df.set_index("timestamp").sort_index()


def read_latest(city_id: str) -> pd.DataFrame:
    """Most recent stored row for one city (single-row DataFrame)."""
    df = read_all(city_ids=[city_id])
    return df.tail(1) if not df.empty else df


SERVING_FG_NAME = "aqi_serving"
SERVING_FG_VERSION = 1
SERVING_FV_NAME = "aqi_serving_fv"
SERVING_FV_VERSION = 1

_serving_fg = None
_fv = None


def get_serving_group():
    """Serving feature group keyed by city_id alone: one current row per city, upserted."""
    global _serving_fg
    if _serving_fg is not None:
        return _serving_fg
    fs = the_connect()
    _serving_fg = fs.get_or_create_feature_group(
        name=SERVING_FG_NAME,
        version=SERVING_FG_VERSION,
        description="Latest row per city for low-latency online serving",
        primary_key=["city_id"],
        online_enabled=True,
        time_travel_format="HUDI",
        stream=True,
        statistics_config=StatisticsConfig(enabled=False),
    )
    return _serving_fg


def write_serving(df: pd.DataFrame):
    """Upsert the latest row per city into the serving group (overwrites by city_id)."""
    if df.empty:
        print("write_serving: empty frame, nothing to write")
        return
    out = df.copy()
    # carry the observation time as a plain column so the serving vector keeps it
    out["generated_at"] = out.index.astype("int64") // 10**9  # epoch seconds, UTC
    fg = get_serving_group()
    fg.insert(_prepare(out), write_options={"wait_for_job": False})


def _get_feature_view():
    global _fv
    if _fv is not None:
        return _fv
    fs = the_connect()
    fg = get_serving_group()
    _fv = fs.get_or_create_feature_view(
        name=SERVING_FV_NAME,
        version=SERVING_FV_VERSION,
        query=fg.select_all(),
    )
    _fv.init_serving()
    return _fv


def read_serving(city_id: str) -> dict:
    """Light single-row lookup via the serving API. No batch engine, low memory."""
    fv = _get_feature_view()
    vec = fv.get_feature_vector(entry={"city_id": city_id})
    if not vec:
        return {}
    cols = fv.schema  # feature order
    names = [f.name for f in cols]
    return dict(zip(names, vec))


# CLI sanity check 
if __name__ == "__main__":
    from datetime import datetime, timedelta, timezone
    from src.cities import get_city
    from src.data_sources import fetch_historical
    from src.feature_engineering import make_inference_frame

    city = get_city("pk-karachi")
    end = datetime.now(timezone.utc).date() - timedelta(days=8)
    start = end - timedelta(days=30)

    print(f"Fetching {city.name} {start} -> {end} ...")
    raw = fetch_historical(city, start.isoformat(), end.isoformat())
    feats = make_inference_frame(raw)
    print(f"feature rows to insert: {len(feats)}")

    print("Connecting to Hopsworks and inserting (first insert can take a few minutes)...")
    insert_features(feats)

    print("Reading latest row back...")
    latest = read_latest(city.city_id)
    if not latest.empty:
        print(latest[["city_id", "aqi", "aqi_dominant"]].to_string())
        print("round trip ok")
    else:
        print("no rows read back — check the Hopsworks UI")