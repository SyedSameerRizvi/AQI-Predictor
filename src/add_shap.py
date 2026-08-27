"""One-off: compute per-horizon SHAP from the already-trained models and write it into the bundle. Does not retrain."""

import shutil
import numpy as np
import shap

from src.feature_store import read_all
from src.feature_engineering import get_feature_columns
from src.config import FORECAST_HORIZONS
from src.pipelines.training_pipeline import load_model, BUNDLE_PATH, save_bundle  # reuse existing io


def main():
    # 1. back up the working bundle first
    shutil.copy(BUNDLE_PATH, BUNDLE_PATH + ".bak")
    print(f"backed up bundle to {BUNDLE_PATH}.bak")

    bundle = load_model()
    feature_cols = bundle["feature_cols"]
    models = bundle["models"]

    # 2. sample real feature rows to explain against
    df = read_all()
    df["city_code"] = df["city_id"].map(bundle["city_codes"]).fillna(-1)
    X = df.dropna(subset=feature_cols)[feature_cols]
    Xs = X.sample(min(2000, len(X)), random_state=42)
    print(f"computing SHAP on {len(Xs)} rows, {len(feature_cols)} features")

    # 3. per-horizon SHAP from the existing models
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
        bundle[f"shap_importance_{h}h"] = ranked
        print(f"  {h}h: top feature {ranked[0]['feature']} ({ranked[0]['importance']:.2f})")

    # 4. re-save the SAME bundle with SHAP added (models unchanged)
    import joblib
    joblib.dump(bundle, BUNDLE_PATH)
    print(f"saved bundle with SHAP to {BUNDLE_PATH}")


if __name__ == "__main__":
    main()