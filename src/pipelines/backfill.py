"""
Backfill historical features for tier-1 cities.

Per city: fetch the full raw history in one continuous frame 
"""

import argparse
import json
import os
from datetime import datetime, timedelta, timezone

from src.cities import active_cities, get_city, City
from src.config import BACKFILL_YEARS
from src.data_sources import fetch_historical
from src.feature_engineering import make_inference_frame
from src.feature_store import insert_features

CHECKPOINT = "backfill_checkpoint.json"
ARCHIVE_LAG_DAYS = 8   # weather archive trails real time


def load_checkpoint() -> dict:
    if os.path.exists(CHECKPOINT):
        with open(CHECKPOINT) as f:
            return json.load(f)
    return {}


def save_checkpoint(cp: dict):
    with open(CHECKPOINT, "w") as f:
        json.dump(cp, f, indent=2)


def backfill_city(city: City, start, end) -> int:
    print(f"[{city.city_id}] fetching {start} -> {end}")
    raw = fetch_historical(city, start.isoformat(), end.isoformat())
    if raw.empty:
        print(f"[{city.city_id}] no raw data returned")
        return 0

    print(f"[{city.city_id}] raw rows: {len(raw)}; building features")
    feats = make_inference_frame(raw)
    if feats.empty:
        print(f"[{city.city_id}] no feature rows after processing")
        return 0

    print(f"[{city.city_id}] inserting {len(feats)} feature rows")
    insert_features(feats)
    return len(feats)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cities", nargs="*", default=None,
                        help="city_ids to backfill (default: all tier-1)")
    parser.add_argument("--years", type=int, default=BACKFILL_YEARS)
    parser.add_argument("--force", action="store_true",
                        help="re-backfill even if checkpoint says done")
    args = parser.parse_args()

    cities = [get_city(c) for c in args.cities] if args.cities else active_cities()

    end = datetime.now(timezone.utc).date() - timedelta(days=ARCHIVE_LAG_DAYS)
    start = end - timedelta(days=365 * args.years)

    print(f"backfilling {len(cities)} city(ies), {start} -> {end}\n")

    cp = load_checkpoint()
    summary = {}
    for city in cities:
        if not args.force and cp.get(city.city_id, {}).get("done"):
            print(f"[{city.city_id}] already done, skipping (use --force to redo)")
            continue
        try:
            n = backfill_city(city, start, end)
            cp[city.city_id] = {
                "done": True,
                "rows": n,
                "at": datetime.now(timezone.utc).isoformat(),
            }
            save_checkpoint(cp)
            summary[city.city_id] = n
        except Exception as exc:  # noqa: BLE001 - isolate per-city failures
            print(f"[{city.city_id}] FAILED: {exc}")
            summary[city.city_id] = f"failed: {exc}"

    print("\nbackfill summary:")
    for cid, result in summary.items():
        print(f"  {cid}: {result}")


if __name__ == "__main__":
    main()