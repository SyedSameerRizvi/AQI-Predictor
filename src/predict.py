"""
predict.py

Live prediction for the trained (tier 1) cities. Loads the model bundle, fetches
recent and forecast data from Open-Meteo, builds features, and returns the
24/48/72 hour AQI forecast with a plain language explanation and the model's
evaluated accuracy for that city and horizon. Only tier 1 cities are served, so
every forecast has real measured accuracy behind it. No web framework here, the
dashboard and the API both import and call these functions.
"""

import os
import json
from datetime import timedelta

import numpy as np
import pandas as pd

from src.cities import get_city, City, active_cities
from src.config import FORECAST_HORIZONS
from src.aqi import aqi_category
from src.pipelines.training_pipeline import load_model
from src.feature_store import read_serving

# cache the bundle and metrics so we load them once per process
_bundle = None
_metrics = None


def _get_bundle():
    global _bundle
    if _bundle is None:
        _bundle = load_model()
    return _bundle


def _get_metrics():
    global _metrics
    if _metrics is None:
        path = os.path.join("models", "aqi_forecaster", "metrics.json")
        if os.path.exists(path):
            with open(path) as f:
                _metrics = pd.DataFrame(json.load(f))
        else:
            _metrics = pd.DataFrame()
    return _metrics


def _accuracy_for(city_id, horizon):
    # the model's evaluated accuracy for this city/horizon
    m = _get_metrics()
    if m.empty:
        return None
    match = m[(m["city"] == city_id) & (m["horizon"] == horizon)]
    if match.empty:
        return None
    r = match.iloc[0]
    return {
        "rmse": round(float(r["rmse"]), 1),
        "mae": round(float(r["mae"]), 1),
        "r2": round(float(r["r2"]), 3),
    }


def _latest_feature_row(city: City, bundle) -> pd.DataFrame:
    vec = read_serving(city.city_id)
    if not vec:
        raise RuntimeError(f"no serving row for {city.city_id}; run the feature pipeline")

    row = pd.DataFrame([vec])
    row["city_code"] = bundle["city_codes"].get(city.city_id, -1)

    # rebuild the UTC timestamp index from the epoch column the pipeline wrote
    if "generated_at" in row.columns and pd.notna(row["generated_at"].iloc[0]):
        ts = pd.to_datetime(row["generated_at"].iloc[0], unit="s", utc=True)
    else:
        ts = pd.Timestamp.now(tz="UTC")  # fallback so valid_at math never breaks
    row.index = pd.DatetimeIndex([ts])

    cols = bundle["feature_cols"]
    usable = row.dropna(subset=[c for c in cols if c in row.columns])
    if usable.empty:
        raise RuntimeError(f"serving row for {city.city_id} missing feature columns")

    return usable.iloc[[-1]]


def explain_prediction(bundle) -> list[str]:
    # turn the top SHAP features into plain language for the dashboard
    imp = bundle.get("shap_importance_24h")
    if not imp:
        return []

    readable = {
        "aqi": "the current AQI level",
        "aqi_lag_1": "the AQI an hour ago",
        "aqi_lag_168": "the AQI at this time last week",
        "pm2_5": "current PM2.5 levels",
        "pm10": "current PM10 levels",
        "city_code": "the city being forecast",
        "aqi_change_1": "how fast AQI is changing",
        "aqi_change_3": "how fast AQI is changing",
        "surface_pressure": "air pressure",
        "wind_u": "wind conditions",
        "temperature_2m": "temperature",
        "aqi_ozone": "current ozone levels",
        "aqi_pm2_5": "current PM2.5 levels",
    }

    out = []
    for item in imp[:5]:
        label = readable.get(item["feature"], item["feature"])
        if label not in out:  # avoid duplicate labels
            out.append(label)
    return out


def predict_city(city_id: str) -> dict:
    """
    Full forecast for one trained city. Returns the current AQI, the 24/48/72
    hour predictions with categories and the model's accuracy, the forecast
    timestamps, and the top feature explanations. Only tier 1 cities are served.
    """
    city = get_city(city_id)
    if city.tier != 1:
        raise ValueError(
            f"{city.name} is not a tier 1 city. Only the trained cities are served: "
            + ", ".join(c.name for c in active_cities())
        )

    bundle = _get_bundle()

    row = _latest_feature_row(city, bundle)
    X = row[bundle["feature_cols"]]
    now_time = row.index[-1]
    current_aqi = float(row["aqi"].iloc[-1])

    predictions = []
    for h in FORECAST_HORIZONS:
        value = float(bundle["models"][h].predict(X)[0])
        value = max(0.0, round(value))  # AQI can't be negative
        name, colour = aqi_category(value)
        predictions.append({
            "horizon_hours": h,
            "valid_at": (now_time + timedelta(hours=h)).isoformat(),
            "aqi": value,
            "category": name,
            "colour": colour,
            "model_accuracy": _accuracy_for(city.city_id, h),
        })

    cur_name, cur_colour = aqi_category(current_aqi)

    return {
        "city_id": city.city_id,
        "city_name": city.name,
        "generated_at": now_time.isoformat(),
        "current": {
            "aqi": round(current_aqi),
            "category": cur_name,
            "colour": cur_colour,
        },
        "forecast": predictions,
        "explanations": explain_prediction(bundle),
    }


def predict_many(city_ids: list[str] = None) -> dict:
    # forecast several cities, isolating failures. defaults to all tier 1 cities.
    if city_ids is None:
        city_ids = [c.city_id for c in active_cities()]
    results, failures = {}, {}
    for cid in city_ids:
        try:
            results[cid] = predict_city(cid)
        except Exception as exc:  # noqa: BLE001
            failures[cid] = str(exc)
    return {"results": results, "failures": failures}


def list_served_cities() -> list[dict]:
    # the cities the dashboard should offer, tier 1 only
    return [{"city_id": c.city_id, "name": c.name} for c in active_cities()]


# --- CLI check --------------------------------------------------------------
# Run:  python -m src.predict

if __name__ == "__main__":
    out = predict_city("pk-islamabad")
    print(json.dumps(out, indent=2))