"""
Update `avg_rating` values for restaurants.

Usage (from `backend/`):
    # set random averages between 1.0 and 5.0
    python -m seeds.update_avg_ratings --mode random --min 1.0 --max 5.0

    # compute averages from existing reviews (uses service helper)
    python -m seeds.update_avg_ratings --mode compute

Default is `random`.
"""
import sys
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models.restaurant import Restaurant


def run_random(min_v: float = 1.0, max_v: float = 5.0):
    db = SessionLocal()
    try:
        restaurants = db.query(Restaurant).all()
        for r in restaurants:
            r.avg_rating = round(random.uniform(min_v, max_v), 2)
            db.add(r)
        db.commit()
        print(f"Assigned random avg_rating to {len(restaurants)} restaurants (range {min_v}-{max_v}).")
    finally:
        db.close()


def run_compute():
    db = SessionLocal()
    try:
        from app.services.restaurant_service import recalculate_restaurant_ratings

        restaurants = db.query(Restaurant.id).all()
        for (rid,) in restaurants:
            try:
                recalculate_restaurant_ratings(db, rid)
            except Exception:
                continue
        print(f"Recalculated avg_rating for {len(restaurants)} restaurants from reviews.")
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["random", "compute"], default="random")
    p.add_argument("--min", type=float, default=1.0)
    p.add_argument("--max", type=float, default=5.0)
    args = p.parse_args()
    if args.mode == "random":
        run_random(args.min, args.max)
    else:
        run_compute()
