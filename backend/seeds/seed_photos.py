"""
Seed restaurant_photos with placeholder images (Unsplash).

Usage (from `backend/`):
    python -m seeds.seed_photos [--replace] [--min 1] [--max 3]

By default this will add photos only for restaurants that have no photos.
Use `--replace` to delete existing photos and replace them.
"""
import sys
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models.restaurant import Restaurant, RestaurantPhoto


def make_unsplash_url(query: str) -> str:
    q = (query or "food").strip().replace(" ", "+")
    # Add a random sig param to avoid caching identical images
    return f"https://source.unsplash.com/800x600/?{q},restaurant,food&sig={random.randint(1,999999)}"


def run(replace: bool = False, min_photos: int = 1, max_photos: int = 3):
    db = SessionLocal()
    try:
        restaurants = db.query(Restaurant).all()
        total = len(restaurants)
        added = 0
        skipped = 0
        replaced = 0

        for idx, r in enumerate(restaurants, start=1):
            photos_q = db.query(RestaurantPhoto).filter(RestaurantPhoto.restaurant_id == r.id)
            existing = photos_q.count()
            if existing and not replace:
                skipped += 1
                continue

            if replace and existing:
                photos_q.delete(synchronize_session=False)
                replaced += 1

            num = random.randint(min_photos, max_photos)
            query = (r.cuisine_type or r.name or "food").split(",")[0]
            for i in range(num):
                url = make_unsplash_url(query)
                photo = RestaurantPhoto(
                    restaurant_id=r.id,
                    file_path=url,
                    caption=None,
                    is_primary=(i == 0),
                )
                db.add(photo)
                added += 1

            if idx % 50 == 0:
                db.commit()

        db.commit()
        print(f"Processed {total} restaurants — added {added} photos, replaced {replaced}, skipped {skipped}.")
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--replace", action="store_true", help="Delete existing photos and replace them")
    p.add_argument("--min", type=int, default=1, help="Minimum photos per restaurant")
    p.add_argument("--max", type=int, default=3, help="Maximum photos per restaurant")
    args = p.parse_args()
    run(replace=args.replace, min_photos=args.min, max_photos=args.max)
