"""
Set random review counts for restaurants (development only).

Run from the `backend/` folder:
    python -m seeds.update_review_counts --min 0 --max 500

This will update the `review_count` column for all restaurants with a random
integer in the provided range. Use for presentation/testing only.
"""
import sys
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models.restaurant import Restaurant


def run(min_count: int = 0, max_count: int = 500):
    db = SessionLocal()
    try:
        restaurants = db.query(Restaurant).all()
        for r in restaurants:
            r.review_count = random.randint(min_count, max_count)  
            r.avg_rating = round(random.uniform(1.0, 5.0), 2) 
            db.add(r)

        db.commit()
        print(f"Updated review_count for {len(restaurants)} restaurants (range {min_count}-{max_count}).")
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--min", type=int, default=0)
    p.add_argument("--max", type=int, default=500)
    args = p.parse_args()
    run(min_count=args.min, max_count=args.max)
