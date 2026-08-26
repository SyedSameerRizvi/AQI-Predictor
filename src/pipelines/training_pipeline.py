"""
training_pipeline.py

Trains the production model: tuned pooled XGBoost, one model per horizon, on all
tier 1 cities read from the feature store. Splits chronologically, evaluates per
city per horizon, saves the model bundle to disk, and tries to register it to the
Hopsworks model registry. Uses fixed hyperparameters chosen during tuning so the
daily run retrains fast instead of searching every time.
"""

import os
import json
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from xgboost import XGBRegressor

from src.feature_store import read_all
from src.feature_engineering import get_feature_columns, TARGETS
from src.config import FORECAST_HORIZONS, MODEL_NAME
from src.evaluation import score_all

load_dotenv()

# best hyperparameters per horizon, chosen during tuning
BEST_PARAMS = {
    24: dict(max_depth=4, learning_rate=0.05, subsample=0.7, colsample_bytree=0.7, min_child_weight=1),
    48: dict(max_depth=4, learning_rate=0.03, subsample=0.7, colsample_bytree=0.9, min_child_weight=1),
    72: dict(max_depth=4, learning_rate=0.10, subsample=0.9, colsample_bytree=0.7, min_child_weight=1),
}

MODEL_DIR = "models/aqi_forecaster"
BUNDLE_PATH = os.path.join(MODEL_DIR, "bundle.joblib")
METRICS_PATH = os.path.join(MODEL_DIR, "metrics.json")


def load_and_split():
    # read all stored cities, keep rows with complete features and targets
    df = read_all()
    cols = get_feature_columns(df) + TARGETS
    data = df.dropna(subset=cols).sort_index()

    # chronological split, same date boundaries for every city
    times = data.index.unique().sort_values()
    train_end = times[int(len(times) * 0.70)]
    val_end = times[int(len(times) * 0.85)]

    train = data[data.index <= train_end].copy()
    val = data[(data.index > train_end) & (data.index <= val_end)].copy()
    test = data[data.index > val_end].copy()

    # stable city code mapping, sorted for reproducibility
    city_codes = {c: i for i, c in enumerate(sorted(data["city_id"].unique()))}
    for part in (train, val, test):
        part["city_code"] = part["city_id"].map(city_codes)

    feature_cols = get_feature_columns(data) + ["city_code"]
    return train, val, test, feature_cols, city_codes


def train_models(train, val, feature_cols):
    X_train, X_val = train[feature_cols], val[feature_cols]
    models = {}
    for h in FORECAST_HORIZONS:
        y_train = train[f"aqi_t_plus_{h}"]
        y_val = val[f"aqi_t_plus_{h}"]
        model = XGBRegressor(
            n_estimators=2000,
            n_jobs=-1, random_state=42,
            early_stopping_rounds=50, eval_metric="rmse",
            **BEST_PARAMS[h],
        )
        model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
        models[h] = model
        print(f"trained horizon {h}h, trees used: {model.best_iteration}")
    return models


def compute_shap(models, train, feature_cols):
    import shap
    X = train[feature_cols]
    # sample for speed; full training set is overkill for global importance
    Xs = X.sample(min(2000, len(X)), random_state=42)
    out = {}
    for h in FORECAST_HORIZONS:
        explainer = shap.TreeExplainer(models[h])
        vals = explainer.shap_values(Xs)
        mean_abs = np.abs(vals).mean(axis=0)
        mean_signed = vals.mean(axis=0)
        ranked = sorted(
            [
                {"feature": f, "importance": float(a), "direction": float(s)}
                for f, a, s in zip(feature_cols, mean_abs, mean_signed)
            ],
            key=lambda r: r["importance"],
            reverse=True,
        )
        out[f"shap_importance_{h}h"] = ranked
    return out


def evaluate(models, test, feature_cols):
    X_test = test[feature_cols]
    rows = []
    for h in FORECAST_HORIZONS:
        preds = models[h].predict(X_test)
        tmp = test.copy()
        tmp["pred"] = preds
        for city_id, g in tmp.groupby("city_id"):
            m = score_all(g[f"aqi_t_plus_{h}"], g["pred"], g["aqi"])
            rows.append({"city": city_id, "horizon": h, **m})
    return pd.DataFrame(rows)


def save_bundle(models, feature_cols, city_codes, metrics_df):
    os.makedirs(MODEL_DIR, exist_ok=True)
    bundle = {
        "models": models,
        "feature_cols": feature_cols,
        "city_codes": city_codes,
        "horizons": FORECAST_HORIZONS,
        "trained_at": datetime.now(timezone.utc).isoformat(),
    }
    joblib.dump(bundle, BUNDLE_PATH)
    metrics_df.to_json(METRICS_PATH, orient="records", indent=2)
    print(f"saved bundle to {BUNDLE_PATH}")


def register_model(metrics_df):
    # try to push to the Hopsworks model registry, do not crash if it fails
    try:
        import hopsworks
        project = hopsworks.login(
            project=os.environ.get("HOPSWORKS_PROJECT"),
            api_key_value=os.environ["HOPSWORKS_API_KEY"],
        )
        mr = project.get_model_registry()
        # a few scalar metrics for the registry
        m24 = metrics_df[metrics_df["horizon"] == 24]
        summary = {
            "rmse_24h_mean": float(m24["rmse"].mean()),
            "r2_24h_mean": float(m24["r2"].mean()),
        }
        model = mr.python.create_model(
            name=MODEL_NAME,
            metrics=summary,
            description="Tuned pooled XGBoost, one model per horizon, 5 cities",
        )
        model.save(MODEL_DIR)
        print("registered model to Hopsworks registry")
    except Exception as exc:  # noqa: BLE001
        print(f"registry step failed (model is still saved locally): {exc}")


def load_model():
    # helper for the dashboard and live pipeline to load the saved bundle
    return joblib.load(BUNDLE_PATH)


def main():
    print("loading data and splitting...")
    train, val, test, feature_cols, city_codes = load_and_split()
    print(f"train {len(train)}, val {len(val)}, test {len(test)}, "
          f"features {len(feature_cols)}, cities {list(city_codes)}")

    print("\ntraining models...")
    models = train_models(train, val, feature_cols)

    print("\nevaluating...")
    metrics_df = evaluate(models, test, feature_cols)
    print(metrics_df.to_string(index=False))

    print("\nsaving bundle...")
    save_bundle(models, feature_cols, city_codes, metrics_df)

    print("\nregistering...")
    register_model(metrics_df)

    print("\ndone.")


if __name__ == "__main__":
    main()