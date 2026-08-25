"""
City registry. Pakistan.

Tiering:
  tier 1 -> full pipeline: 2-year backfill, hourly updates, in training,
            instant dashboard load.
  tier 2 -> selectable, scored live on demand with the global model.
            No stored history.
Promote a city by changing its tier here, one line.
"""


from dataclasses import dataclass

@dataclass(frozen=True)
class City:
    city_id: str
    name: str
    lat: float
    lon: float
    timezone: str
    tier: str  # 1 = full pipeline, 2 = on-demand scoring only

CITIES = [
    City("pk-karachi",    "Karachi",    24.8607, 67.0011, "Asia/Karachi", tier=1),
    City("pk-lahore",     "Lahore",     31.5204, 74.3587, "Asia/Karachi", tier=1),
    City("pk-islamabad",  "Islamabad",  33.6844, 73.0479, "Asia/Karachi", tier=1),
    City("pk-faisalabad", "Faisalabad", 31.4504, 73.1350, "Asia/Karachi", tier=1),
    City("pk-rawalpindi", "Rawalpindi", 33.5651, 73.0169, "Asia/Karachi", tier=2),
    City("pk-multan",     "Multan",     30.1575, 71.5249, "Asia/Karachi", tier=2),
    City("pk-peshawar",   "Peshawar",   34.0151, 71.5249, "Asia/Karachi", tier=1),
    City("pk-quetta",     "Quetta",     30.1798, 66.9750, "Asia/Karachi", tier=1),
    City("pk-hyderabad",  "Hyderabad",  25.3960, 68.3578, "Asia/Karachi", tier=2),
    City("pk-gujranwala", "Gujranwala", 32.1877, 74.1945, "Asia/Karachi", tier=2),
]

_BY_ID = {C.city_id : C for C in CITIES}

def get_city(city_id: str) -> City:
    """Look up one city by its slug. Raises KeyError if not found."""
    return _BY_ID[city_id]

def all_cities() -> list[City]:
    """Every city in the registry, any tier."""
    return list(CITIES)

def active_cities() -> list[City]:
    """Tier 1 only — the cities with the full pipeline and stored history."""
    return [c for c in CITIES if c.tier == 1]

