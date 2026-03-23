"""
Seed synthetic reviews for restaurants in the local database.

Run from the backend folder like:
    python -m seeds.seed_reviews --min 1 --max 4 --users 20 --only-empty

This will create between min and max reviews per restaurant (for restaurants with no reviews
when --only-empty is provided). Reviews are created without linking to real users (user_id=None)
but provide author names so they appear as local reviews. Ratings and text are randomized.
"""
import sys
import random
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from faker import Faker

from app.database import SessionLocal
from app.models.restaurant import Restaurant
from app.models.review import Review
from app.models.review import ReviewPhoto
from app.services.restaurant_service import recalculate_restaurant_ratings


fake = Faker()


def run(min_per=1, max_per=3, num_users=0, only_empty=False):
    db = SessionLocal()
    try:
        restaurants = db.query(Restaurant).all()
        created = 0
        for r in restaurants:
            existing_count = db.query(Review).filter(Review.business_id == r.id).count()
            if only_empty and existing_count > 0:
                continue

            target = random.randint(min_per, max_per)
            # if restaurant already has reviews, only add up to target additional
            to_create = target if existing_count == 0 else max(0, target - existing_count)
            for _ in range(to_create):
                rating = random.randint(1, 5)
                title = fake.sentence(nb_words=6)
                body = fake.paragraph(nb_sentences=random.randint(1, 4))
                visited = date.today() - timedelta(days=random.randint(0, 1000))
                review = Review(
                    business_id=r.id,
                    user_id=None,
                    author_name=fake.name(),
                    rating=rating,
                    title=title,
                    body=body,
                    visited_at=visited,
                    source="local",
                )
                db.add(review)
                created += 1

                # Occasionally add an inline review photo (as ReviewPhoto or RestaurantPhoto)
                if random.random() < 0.12:
                    # store as a review_photo row referencing the review (needs review id, so flush)
                    db.flush()
                    purl = f"https://picsum.photos/seed/rev{random.randint(1,10000)}/640/480"
                    rp = ReviewPhoto(review_id=review.id, file_path=purl)
                    db.add(rp)

            if created % 50 == 0:
                db.commit()

        db.commit()

        # Recalculate ratings for all restaurants (best-effort)
        for r in restaurants:
            recalculate_restaurant_ratings(db, r.id)

        print(f"Created {created} reviews for {len(restaurants)} restaurants")
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--min", type=int, default=1)
    p.add_argument("--max", type=int, default=3)
    p.add_argument("--users", type=int, default=0, help="(ignored) kept for compatibility")
    p.add_argument("--only-empty", action="store_true", help="Only add reviews to restaurants that have no reviews yet")
    args = p.parse_args()
    run(min_per=args.min, max_per=args.max, num_users=args.users, only_empty=args.only_empty)
