"""
Update `businesses.image_url` from `restaurant_photos.file_path` for primary photos.

Run from the `backend/` folder:
    python -m seeds.update_business_image_urls

This will set `businesses.image_url` = `/uploads/...` (or whatever is in `restaurant_photos.file_path`)
for rows where `restaurant_photos.is_primary` is true.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models.restaurant import Restaurant, RestaurantPhoto


def run():
    db = SessionLocal()
    try:
        primaries = db.query(RestaurantPhoto).filter(RestaurantPhoto.is_primary == True).all()
        updated = 0
        for p in primaries:
            rest = db.query(Restaurant).filter(Restaurant.id == p.restaurant_id).first()
            if not rest:
                continue
            if rest.image_url != p.file_path:
                rest.image_url = p.file_path
                db.add(rest)
                updated += 1
        db.commit()
        print(f"Updated {updated} businesses.image_url from primary photos")
    finally:
        db.close()


if __name__ == "__main__":
    run()
