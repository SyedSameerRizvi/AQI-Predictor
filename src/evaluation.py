"""
Metrics for scoring AQI forecasts, computed per city and per horizon.
Provides RMSE, MAE, and R2 (the mentor benchmark metrics), plus a skill score
that measures improvement over a baseline, a target checker that flags whether
a result clears the benchmark (R2 >= 0.7, RMSE <= 30, MAE <= 20), and a helper
to collect all results into one comparison table.
"""

# metrics for model evaluation, per horizon and per city

import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score


def rmse(y_true, y_pred):
    return np.sqrt(mean_squared_error(y_true, y_pred))


def mae(y_true, y_pred):
    return mean_absolute_error(y_true, y_pred)


def r2(y_true, y_pred):
    return r2_score(y_true, y_pred)


def skill_score(y_true, y_pred, y_baseline):
    # how much better than the baseline, 0 = same, 1 = perfect
    mse_model = mean_squared_error(y_true, y_pred)
    mse_base = mean_squared_error(y_true, y_baseline)
    if mse_base == 0:
        return 0.0
    return 1 - (mse_model / mse_base)


def score_all(y_true, y_pred, y_baseline=None):
    # returns a dict of all metrics for one set of predictions
    out = {
        "rmse": rmse(y_true, y_pred),
        "mae": mae(y_true, y_pred),
        "r2": r2(y_true, y_pred),
    }
    if y_baseline is not None:
        out["skill"] = skill_score(y_true, y_pred, y_baseline)
    return out


def check_targets(metrics, r2_min=0.7, rmse_max=30, mae_max=20):
    # checks a metrics dict against the mentor benchmark, returns pass/fail
    return {
        "r2_ok": metrics["r2"] >= r2_min,
        "rmse_ok": metrics["rmse"] <= rmse_max,
        "mae_ok": metrics["mae"] <= mae_max,
        "all_ok": (metrics["r2"] >= r2_min
                   and metrics["rmse"] <= rmse_max
                   and metrics["mae"] <= mae_max),
    }


def results_table(rows):
    # rows is a list of dicts, returns a sorted dataframe for display
    df = pd.DataFrame(rows)
    return df.sort_values(["city", "horizon", "model"]).reset_index(drop=True)