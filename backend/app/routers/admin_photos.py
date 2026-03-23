from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import random

from app.database import get_db
from app.models.restaurant import Restaurant, RestaurantPhoto

router = APIRouter()


@router.post("/seed")
def seed_photos(replace: bool = False, min: int = 1, max: int = 3, db: Session = Depends(get_db)):
    restaurants = db.query(Restaurant).all()
    added = 0
    replaced = 0
    skipped = 0

    for idx, r in enumerate(restaurants, start=1):
        photos_q = db.query(RestaurantPhoto).filter(RestaurantPhoto.restaurant_id == r.id)
        existing = photos_q.count()
        if existing and not replace:
            skipped += 1
            continue
        if replace and existing:
            photos_q.delete(synchronize_session=False)
            replaced += 1

        num = random.randint(min, max)
        query = (r.cuisine_type or r.name or "food").split(",")[0]
        for i in range(num):
            url = f"https://source.unsplash.com/800x600/?{query},restaurant,food&sig={random.randint(1,999999)}"
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
    return {"processed": len(restaurants), "added": added, "replaced": replaced, "skipped": skipped}
