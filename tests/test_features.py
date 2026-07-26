"""
Leakage tests. The core invariant: a feature at time t must not depend on any
data after it.
"""


import numpy as np
import pandas as pd
import pytest

from src.feature_engineering import build_features, get_feature_columns, TARGETS

def the_synthetic_city(city_id, n=400, seed=0):
    """A function to generate a synthetic city with a given number of samples and a random seed."""
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2024-01-01", periods=n, freq="h", tz="UTC")
    df = pd.DataFrame({
        "city_id": city_id,
        "pm2_5": rng.uniform(20, 200, n),
        "pm10": rng.uniform(30, 300, n),
        "carbon_monoxide": rng.uniform(100, 1000, n),
        "nitrogen_dioxide": rng.uniform(5, 80, n),
        "sulphur_dioxide": rng.uniform(2, 40, n),
        "ozone": rng.uniform(10, 120, n),
        "temperature_2m": rng.uniform(10, 35, n),
        "dew_point_2m": rng.uniform(5, 25, n),
        "surface_pressure": rng.uniform(1000, 1020, n),
        "wind_speed_10m": rng.uniform(0, 25, n),
        "wind_direction_10m": rng.uniform(0, 360, n),
        "precipitation": rng.uniform(0, 5, n),
        "cloud_cover": rng.uniform(0, 100, n),
    }, index=idx)
    return df

def test_no_leakage_in_features_in_future():
    """Test that the features do not leak information from the future."""
    df = the_synthetic_city("pk-karachi")
    cutoff = df.index[250] #well inside the frame 

    feats_a = build_features(df)
    fcols = get_feature_columns(feats_a)
    row_a = feats_a.loc[cutoff, fcols]

    #wreck the future
    df2 = df.copy()
    future = df2.index > cutoff
    df2.loc[future, "pm2_5"] = 9999.0
    df2.loc[future, "ozone"] = 9999.0
    df2.loc[future, "wind_speed_10m"] = 0.0

    feats_b = build_features(df2)
    row_b = feats_b.loc[cutoff, fcols]

    pd.testing.assert_series_equal(row_a, row_b, check_names=False,
                                   obj="Feature row cutoff must not depend on the future data",
                                   )

    def test_targets_do_look_forward():
        """Test that the targets SHOULD change when the future changes."""
        df = the_synthetic_city("pk-karachi")
        cutoff = df.index[250] #well inside the frame

        t_a = build_features(df).loc[cutoff, TARGETS]

        df2 = df.copy()
        df2.loc[df2.index > cutoff, "pm2_5"] = 9999.0
        t_b = build_features(df2).loc[cutoff, TARGETS]

        # at least one horizon's target must have moved
        assert not np.allclose(t_a.values, t_b.values, equal_nan=True)

def test_no_cross_city_leakage():
    """Test that features from one city do not leak into another city's features."""
    
    a = the_synthetic_city("pk-karachi", seed=1)
    a["pm2_5"] = np.linspace(10, 90, len(a))        # city A: 10..90
    b = the_synthetic_city("pk-lahore", seed=2)
    b["pm2_5"] = np.linspace(500, 540, len(b))       # city B: 500..540

    feats = build_features(pd.concat([a, b]))
    a_feats = feats[feats["city_id"] == "pk-karachi"].dropna(subset=["pm2_5_lag_24"])

    # City A's pm2_5 lag must stay in City A's range (<=90), never City B's ~500s.
    assert a_feats["pm2_5_lag_24"].max() <= 90
    assert a_feats["pm2_5_lag_24"].min() >= 10