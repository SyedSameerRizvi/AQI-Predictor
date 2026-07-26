"""
Locks the AQI math against known values from the EPA breakpoint table.
If any of these fail, the calculation is wrong and everything downstream is too.
Run: pytest tests/test_aqi.py -v
"""

import math
import pytest
from src.aqi import (
    concentration_to_subindex,
    ugm3_to_native,
    aqi_category,
)


# Exact band-edge points, in each pollutant's NATIVE unit 
# At a breakpoint edge the formula collapses to the index value, so these are
# Unambiguous and easy to verify by hand against the table.

@pytest.mark.parametrize("pollutant, concentration, expected", [
    ("pm2_5", 9.0, 50),      # top of Good
    ("pm2_5", 35.5, 101),    # bottom of USG
    ("pm2_5", 55.5, 151),    # bottom of Unhealthy
    ("pm2_5", 12.0, 56),     # mid-band interpolation (AirNow gives 56)
    ("pm10", 155, 101),
    ("carbon_monoxide", 4.5, 51),
    ("carbon_monoxide", 9.4, 100),
    ("ozone", 0.055, 51),
    ("sulphur_dioxide", 36, 51),
    ("nitrogen_dioxide", 54, 51),
    ("nitrogen_dioxide", 53, 50),   # top of Good
])
def test_subindex_known_values(pollutant, concentration, expected):
    assert concentration_to_subindex(pollutant, concentration) == expected


def test_missing_value_returns_none():
    assert concentration_to_subindex("pm2_5", None) is None
    assert concentration_to_subindex("pm2_5", float("nan")) is None


# Unit Conversion 
# NO2 at 100 ug/m3 -> ppb = 100 * 24.45 / 46.01 = 53.14 ppb

def test_ugm3_to_ppb_no2():
    ppb = ugm3_to_native("nitrogen_dioxide", 100.0)
    assert math.isclose(ppb, 53.14, abs_tol=0.05)

def test_pm_is_not_converted():
    # PM stays in ug/m3 untouched
    assert ugm3_to_native("pm2_5", 42.0) == 42.0


# Categories 

def test_categories():
    assert aqi_category(25)[0] == "Good"
    assert aqi_category(75)[0] == "Moderate"
    assert aqi_category(125)[0] == "Unhealthy for Sensitive Groups"
    assert aqi_category(175)[0] == "Unhealthy"
    assert aqi_category(250)[0] == "Very Unhealthy"
    assert aqi_category(400)[0] == "Hazardous"