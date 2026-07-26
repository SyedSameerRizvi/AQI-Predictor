"""
Feature engineering: raw merged dataframe -> model-ready features + targets.

Two structural safeguards:
  1. Every city is processed on its own frame, so lags/rolls can never span
     across cities (Delhi's history leaking into Karachi's lags is a classic,
     invisible bug).
  2. All lag / rolling / change features look strictly backward (trailing
     windows ending at t). The targets are the only thing that looks forward,
     and they are the actual observed future AQI — which is exactly what a
     target should be.

"""

import numpy as np
import pandas as pd

from src.aqi import add_aqi_columns
from src.cities import get_city
from src.config import FORECAST_HORIZONS


LAG_BASES = ["aqi", "pm2_5"]                       # columns we take lags of
LAG_HOURS = [1, 2, 3, 6, 12, 24, 48, 72, 168]     # incl. one week (168h)
ROLL_WINDOWS = [6, 12, 24, 72]                     # rolling stat windows (h)
CHANGE_HOURS = [1, 3, 6, 24]                       # rate-of-change windows (h)

TARGETS = [f"aqi_t_plus_{h}" for h in FORECAST_HORIZONS]  # aqi_t_plus_24/48/72


def _time_features(local_index: pd.DatetimeIndex) -> pd.DataFrame:
    """
    Calendar features from LOCAL time. Local, not UTC, because rush-hour and
    daily pollution cycles are local-clock phenomena. Hour and month are encoded
    cyclically (sin/cos) so a model sees hour 23 and hour 0 as adjacent, not
    23 units apart.
    """
    hour = local_index.hour
    month = local_index.month
    dow = local_index.dayofweek  # Monday=0 to Sunday=6

    return pd.DataFrame({
        "hour": hour,
        "day_of_week": dow,
        "day_of_month": local_index.day,
        "month": month,
        "is_weekend": (dow >= 5).astype(int),  # Sat/Sun weekend in Pakistan
        "hour_sin": np.sin(2 * np.pi * hour / 24),
        "hour_cos": np.cos(2 * np.pi * hour / 24),
        "month_sin": np.sin(2 * np.pi * (month - 1) / 12),
        "month_cos": np.cos(2 * np.pi * (month - 1) / 12),
    }, index=local_index)


def _weather_features(g: pd.DataFrame) -> pd.DataFrame:
    """
    Weather is derived from features. These use the current hour's weather, which is
    legitimately known at prediction time because at inference we have a real
    weather forecast for the horizon. (Pollutant values are NOT future known,
    which is why it never takes future pollutant values anywhere.)
    """
    out = pd.DataFrame(index=g.index)

    # Wind as u/v components. Direction in degrees is circular (359 and 1 are adjacent), so a model must not see it as a raw number. Meteorological
    # convention: direction is where wind comes FROM, hence the minus signs.
    if "wind_speed_10m" in g and "wind_direction_10m" in g:
        rad = np.deg2rad(g["wind_direction_10m"])
        out["wind_u"] = -g["wind_speed_10m"] * np.sin(rad)
        out["wind_v"] = -g["wind_speed_10m"] * np.cos(rad)

    # How close air is to saturation 
    if "temperature_2m" in g and "dew_point_2m" in g:
        out["temp_dewpoint_spread"] = g["temperature_2m"] - g["dew_point_2m"]

    # Stagnation proxy: high pressure + low wind means poor dispersion, so this
    # Rises when the air is still. +1 avoids divide by zero at dead calm.
    if "surface_pressure" in g and "wind_speed_10m" in g:
        out["stagnation_index"] = g["surface_pressure"] / (g["wind_speed_10m"] + 1.0)

    return out


def _features_for_one_city(g: pd.DataFrame, city_id: str) -> pd.DataFrame:
    """
    Build the full feature+target frame for a SINGLE city's time ascending data.
    Processing one city at a time is what guarantees no cross city leakage.
    """
    g = g.sort_index().copy()

    # 1. Compute AQI for this city alone (trailing EPA windows, past-looking).
    g = add_aqi_columns(g)

    # 2. Start assembling features. Keep raw weather + current pollutant values
    # And current AQI: all are known at time t and are valid inputs.
    feats = g.copy()

    # 3. Calendar features from local time.
    tz = get_city(city_id).timezone
    local_index = g.index.tz_convert(tz)
    tf = _time_features(local_index)
    tf.index = g.index  # keep the canonical UTC index for alignment
    feats = feats.join(tf)

    # 4. Weather-derived.
    feats = feats.join(_weather_features(g))

    # 5. Lags strictly past.
    for base in LAG_BASES:
        if base in g:
            for k in LAG_HOURS:
                feats[f"{base}_lag_{k}"] = g[base].shift(k)

    # 6. Rolling stats of AQI over trailing windows ending at t (past+present).
    for w in ROLL_WINDOWS:
        feats[f"aqi_roll_mean_{w}"] = g["aqi"].rolling(w, min_periods=1).mean()
        feats[f"aqi_roll_std_{w}"] = g["aqi"].rolling(w, min_periods=2).std()
    feats["aqi_roll_min_24"] = g["aqi"].rolling(24, min_periods=1).min()
    feats["aqi_roll_max_24"] = g["aqi"].rolling(24, min_periods=1).max()

    # 7. Rate of change: how fast AQI moved over the last h hours (the brief's "AQI change rate"). Uses past values only.
    for h in CHANGE_HOURS:
        feats[f"aqi_change_{h}"] = g["aqi"] - g["aqi"].shift(h)

    # 8. Interaction: time of day crossed with wind, since dispersion and the daily emission cycle interact.
    if "wind_speed_10m" in g:
        feats["hour_x_windspeed"] = local_index.hour.values * g["wind_speed_10m"]

    # 9. Targets the ONLY forward looking thing. Observed AQI h hours into the future. This is the label, by design.
    for h in FORECAST_HORIZONS:
        feats[f"aqi_t_plus_{h}"] = g["aqi"].shift(-h)

    return feats


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Full feature pipeline. Takes the RAW merged frame from data_sources
    (pollutants + weather + city_id, UTC index) and returns features + targets.
    Handles one or many cities; each is processed independently.
    """
    if df.empty:
        return df
    frames = [_features_for_one_city(g, cid) for cid, g in df.groupby("city_id")]
    return pd.concat(frames).sort_index()


# Selecting columns for modelling

def get_feature_columns(df: pd.DataFrame) -> list[str]:
    """
    Numeric feature columns: everything numeric except the targets. city_id and
    aqi_dominant are strings and drop out automatically.
    """
    numeric = df.select_dtypes(include=[np.number]).columns
    return [c for c in numeric if c not in TARGETS]


def make_training_frame(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rows usable for training: complete features AND all targets present. The
    first 168 rows per city (incomplete lags) and the last 72 (no target yet)
    fall away here.
    """
    feats = build_features(df)
    cols = get_feature_columns(feats) + TARGETS
    return feats.dropna(subset=cols)


def make_inference_frame(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rows usable for prediction: complete features, targets NOT required (the
    most recent rows have no future yet those are exactly what to predict on).
    """
    feats = build_features(df)
    return feats.dropna(subset=get_feature_columns(feats))


# CLI sanity check 

if __name__ == "__main__":
    from datetime import datetime, timedelta, timezone
    from src.cities import get_city
    from src.data_sources import fetch_historical

    city = get_city("pk-karachi")
    end = datetime.now(timezone.utc).date() - timedelta(days=8)
    start = end - timedelta(days=30)  # 30 days so lags up to 168h have data

    print(f"Fetching {city.name} {start} -> {end} ...")
    raw = fetch_historical(city, start.isoformat(), end.isoformat())
    print(f"raw rows: {len(raw)}")

    feats = build_features(raw)
    train = make_training_frame(raw)
    fcols = get_feature_columns(feats)

    print(f"feature rows (all): {len(feats)}")
    print(f"trainable rows (complete): {len(train)}")
    print(f"number of feature columns: {len(fcols)}")
    print(f"targets: {TARGETS}")
    print("\nsample feature columns:", fcols[:12])
    if not train.empty:
        print("\nlast trainable row, a few features + targets:")
        show = ["aqi", "aqi_lag_24", "aqi_roll_mean_24", "aqi_change_24"] + TARGETS
        print(train[show].tail(3).to_string())


