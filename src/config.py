"""
Central configuration for the AQI forecasting system.
"""


# Predict AQI this many hours into the future. One model per horizon.
FORECAST_HORIZONS = [24, 48, 72]  # 1, 2, and 3 days ahead

# Pollutants to be pulled from Open-Meteo (their API variable names) 
POLLUTANTS = [
    "pm2_5",
    "pm10",
    "carbon_monoxide",
    "nitrogen_dioxide",
    "sulphur_dioxide",
    "ozone",
]

# Weather variables to be pulled from Open-Meteo (their API variable names) 
WEATHER_VARS = [
    "temperature_2m",
    "relative_humidity_2m",
    "dew_point_2m",
    "surface_pressure",
    "wind_speed_10m",
    "wind_direction_10m",
    "precipitation",
    "cloud_cover",
]

#  AQI alert thresholds (US EPA scale)
# Dashboard raises an alert when a predicted value crosses this.
ALERT_THRESHOLD = 150  # "Unhealthy" band and above

#  Backfill window 
BACKFILL_YEARS = 2  # how much history to scrape for training

# Timezone to use for storing data in Hopsworks feature store.
STORAGE_TIMEZONE = "UTC"

# Hopsworks feature store / model registry names 
FEATURE_GROUP_NAME = "aqi_features"
FEATURE_GROUP_VERSION = 1
FEATURE_VIEW_NAME = "aqi_feature_view"
MODEL_NAME = "aqi_forecaster"

# Open-Meteo API endpoints
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
WEATHER_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
WEATHER_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"