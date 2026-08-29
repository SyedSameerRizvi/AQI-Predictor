"""
Hourly feature pipeline. For each tier-1 city we fetch the recent window from
Open-Meteo, build features, and upsert them to the Hopsworks feature store.
This runs on a schedule so the dashboard reads features from the store and
never calls Open-Meteo at request time.

Writes to two groups:
- aqi_features (history, keyed by city_id + timestamp) for retraining
- aqi_serving (latest row per city, keyed by city_id) for low-latency reads
"""

import pandas as pd

from src.cities import active_cities
from src.data_sources import fetch_forecast, fetch_many
from src.feature_engineering import make_inference_frame
from src.feature_store import insert_features, write_serving


PAST_DAYS = 10      # covers the 168h lag window with margin
FORECAST_DAYS = 3   # future weather for the prediction window


def run() -> dict:
    cities = active_cities()
    print(f"feature pipeline: {len(cities)} cities")

    results, failures = fetch_many(
        cities,
        fetch_forecast,
        past_days=PAST_DAYS,
        forecast_days=FORECAST_DAYS,
    )

    for city_id, reason in failures.items():
        print(f"[{city_id}] fetch failed: {reason}")

    raws = [df for df in results.values() if not df.empty]
    if not raws:
        print("no data fetched, nothing to write")
        return {"written": 0, "serving": 0, "failures": failures}

    combined = pd.concat(raws).sort_index()
    feats = make_inference_frame(combined)
    if feats.empty:
        print("no usable feature rows after processing")
        return {"written": 0, "serving": 0, "failures": failures}

    # full history group (retraining)
    print(f"writing {len(feats)} rows across {len(raws)} cities")
    insert_features(feats)

    # latest row per city -> serving group (low-latency reads)
    now = pd.Timestamp.now(tz="UTC")
    latest = feats[feats.index <= now].groupby("city_id").tail(1)
    print(f"writing {len(latest)} serving rows")
    write_serving(latest)

    return {"written": len(feats), "serving": len(latest), "failures": failures}


if __name__ == "__main__":
    out = run()
    print(
        f"\ndone: wrote {out['written']} history rows, "
        f"{out['serving']} serving rows, {len(out['failures'])} failures"
    )