
"""
US EPA Air Quality Index calculation.

Two layers:
  1. Pure functions on single values, in the EPA's own units.
  2. A dataframe helper that takes Open-Meteo hourly data (all in ug/m3), applies
     the correct per-pollutant averaging window, converts gases to ppm/ppb, and
     returns overall AQI + the pollutant driving it.
"""



import math
import numpy as np
import pandas as pd


BREAKPOINTS = {
    # PM: EPA breakpoints are already in ug/m3, so no conversion. 24h average.
    "pm2_5": [
        (0.0, 9.0, 0, 50),
        (9.1, 35.4, 51, 100),
        (35.5, 55.4, 101, 150),
        (55.5, 125.4, 151, 200),
        (125.5, 225.4, 201, 300),
        (225.5, 325.4, 301, 500),
    ],
    "pm10": [
        (0, 54, 0, 50),
        (55, 154, 51, 100),
        (155, 254, 101, 150),
        (255, 354, 151, 200),
        (355, 424, 201, 300),
        (425, 604, 301, 500),
    ],
    # CO breakpoints are in ppm, 8h average.
    "carbon_monoxide": [
        (0.0, 4.4, 0, 50),
        (4.5, 9.4, 51, 100),
        (9.5, 12.4, 101, 150),
        (12.5, 15.4, 151, 200),
        (15.5, 30.4, 201, 300),
        (30.5, 50.4, 301, 500),
    ],
    # O3 breakpoints in ppm, 8h average. The 8h table only defines up to 300;
    # values above that are rare and would need the 1h table. We cap at the top
    # of the 8h range and document it 8h ozone above 0.2 ppm essentially never
    # occurs in this dataset.
    "ozone": [
        (0.000, 0.054, 0, 50),
        (0.055, 0.070, 51, 100),
        (0.071, 0.085, 101, 150),
        (0.086, 0.105, 151, 200),
        (0.106, 0.200, 201, 300),
    ],
    # SO2 breakpoints in ppb, 1h average.
    "sulphur_dioxide": [
        (0, 35, 0, 50),
        (36, 75, 51, 100),
        (76, 185, 101, 150),
        (186, 304, 151, 200),
        (305, 604, 201, 300),
        (605, 1004, 301, 500),
    ],
    # NO2 breakpoints in ppb, 1h average.
    "nitrogen_dioxide": [
        (0, 53, 0, 50),
        (54, 100, 51, 100),
        (101, 360, 101, 150),
        (361, 649, 151, 200),
        (650, 1249, 201, 300),
        (1250, 2049, 301, 500),
    ],
}

# Unit conversion for the gases
# Open-Meteo returns ALL pollutants in ug/m3. But EPA gas breakpoints are in
# ppm (CO, O3) or ppb (SO2, NO2). Convert before applying the breakpoints.
#
#   ppb = (ug/m3) * MOLAR_VOLUME / molecular_weight
#   ppm = ppb / 1000
#
# MOLAR_VOLUME is the volume of one mole of ideal gas at 25 C and 1 atm.

MOLAR_VOLUME = 24.45  # litres per mole at 25 C, 1 atm

MOLECULAR_WEIGHTS = {   # g/mol
    "ozone": 48.00,
    "carbon_monoxide": 28.01,
    "sulphur_dioxide": 64.07,
    "nitrogen_dioxide": 46.01,
}

# What native unit each breakpoint table expects.
NATIVE_UNIT = {
    "pm2_5": "ug/m3",
    "pm10": "ug/m3",
    "carbon_monoxide": "ppm",
    "ozone": "ppm",
    "sulphur_dioxide": "ppb",
    "nitrogen_dioxide": "ppb",
}

# EPA truncation rule applied to the averaged concentration before lookup.
TRUNCATE_DECIMALS = {
    "pm2_5": 1,
    "pm10": 0,
    "carbon_monoxide": 1,
    "ozone": 3,
    "sulphur_dioxide": 0,
    "nitrogen_dioxide": 0,
}

# Averaging window in hours for the dataframe helper.
AVERAGING_HOURS = {
    "pm2_5": 24,
    "pm10": 24,
    "carbon_monoxide": 8,
    "ozone": 8,
    "sulphur_dioxide": 1,
    "nitrogen_dioxide": 1,
}

# EPA category bands (name, hex colour)

CATEGORIES = [
    (0, 50, "Good", "#00e400"),
    (51, 100, "Moderate", "#ffff00"),
    (101, 150, "Unhealthy for Sensitive Groups", "#ff7e00"),
    (151, 200, "Unhealthy", "#ff0000"),
    (201, 300, "Very Unhealthy", "#8f3f97"),
    (301, 10_000, "Hazardous", "#7e0023"),
]


def ugm3_to_native(pollutant: str, value_ugm3: float) -> float:
    """Convert an Open-Meteo ug/m3 reading into the unit its breakpoints use."""
    unit = NATIVE_UNIT[pollutant]
    if unit == "ug/m3":
        return value_ugm3
    ppb = value_ugm3 * MOLAR_VOLUME / MOLECULAR_WEIGHTS[pollutant]
    return ppb / 1000.0 if unit == "ppm" else ppb


def _truncate(value: float, decimals: int) -> float:
    """EPA truncates (not rounds) the concentration before the breakpoint lookup."""
    factor = 10 ** decimals
    return math.floor(value * factor) / factor


def concentration_to_subindex(pollutant: str, concentration_native: float):
    """
    Sub-index for one pollutant from a concentration already in its native unit
    and already averaged over the right window. Returns an int, or None if the
    value is missing or above the highest defined breakpoint.
    """
    if concentration_native is None or (isinstance(concentration_native, float)
                                        and math.isnan(concentration_native)):
        return None

    c = _truncate(concentration_native, TRUNCATE_DECIMALS[pollutant])

    for c_low, c_high, i_low, i_high in BREAKPOINTS[pollutant]:
        if c_low <= c <= c_high:
            aqi = (i_high - i_low) / (c_high - c_low) * (c - c_low) + i_low
            return round(aqi)

    # Above the top defined breakpoint (e.g. 8h ozone > 0.200 ppm). Clamp to the
    # top band's index rather than inventing a number.
    return BREAKPOINTS[pollutant][-1][3]


def aqi_category(aqi_value: float):
    """Return (name, hex_colour) for an AQI value, for the dashboard."""
    if aqi_value is None or (isinstance(aqi_value, float) and math.isnan(aqi_value)):
        return ("Unknown", "#cccccc")
    for low, high, name, colour in CATEGORIES:
        if low <= aqi_value <= high:
            return (name, colour)
    return ("Hazardous", "#7e0023")


def add_aqi_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Take a time-ascending hourly dataframe with pollutant columns in ug/m3
    (pm2_5, pm10, carbon_monoxide, ozone, sulphur_dioxide, nitrogen_dioxide)
    and add:
        aqi                -> overall AQI (max of sub-indices) per hour
        aqi_dominant       -> which pollutant drove it
        aqi_<pollutant>    -> each sub-index, for inspection

    The trailing rolling averages (past 24h/8h/1h ending at each hour) are the
    correct EPA windows and use only past+current data, so this is not leakage.
    Index must be a sorted DatetimeIndex.
    """
    df = df.sort_index().copy()
    subindex_cols = []

    for pollutant, window in AVERAGING_HOURS.items():
        if pollutant not in df.columns:
            continue  # some cities / hours may lack a pollutant; skip it

        # trailing average over the EPA window, ending at the current hour
        averaged = df[pollutant].rolling(window=window, min_periods=1).mean()
        # convert to native unit, then to sub-index, row by row
        native = averaged.map(lambda v: ugm3_to_native(pollutant, v))
        col = f"aqi_{pollutant}"
        df[col] = native.map(lambda v: concentration_to_subindex(pollutant, v))
        subindex_cols.append(col)

    sub = df[subindex_cols]
    df["aqi"] = sub.max(axis=1)
    # name of the pollutant column that hit the max (strip the "aqi_" prefix)
    df["aqi_dominant"] = sub.idxmax(axis=1).str.replace("aqi_", "", regex=False)
    return df

