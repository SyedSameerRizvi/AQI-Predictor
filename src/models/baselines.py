"""
Naive forecast baselines used as the yardstick for every real model.
Persistence predicts that AQI h hours from now equals the current AQI.
Seasonal naive predicts it equals the AQI at the same hour one week ago.
If a trained model cannot beat these, that is the finding and we report it.
"""

import numpy as np


def persistence_prediction(current_aqi):
    # predict future AQI = current AQI, works for any horizon
    return np.asarray(current_aqi)


def seasonal_naive_prediction(aqi_last_week):
    # predict future AQI = AQI at the same hour 7 days ago
    return np.asarray(aqi_last_week)