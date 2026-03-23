"""
Synthetic Yelp-like seeder for local development.

Run from the `backend/` folder:
    python -m seeds.seed_fake --restaurants 60 --reviews 220

This generates realistic-looking restaurants, hours, photos and reviews using Faker
and placeholder images. Safe for development and does not require external APIs.
"""
import sys
import random
from datetime import date, timedelta, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from faker import Faker
from slugify import slugify

from app.database import SessionLocal
from app.models.user import User
from app.models.restaurant import Restaurant, RestaurantPhoto, RestaurantHours
from app.models.review import Review
from app.models.enums import DayOfWeekEnum, PriceRangeEnum

fake = Faker()


def parse_time_str(t: str):
    # returns HH:MM string
    return t


def make_slug(name: str, suffix: int) -> str:
    return f"{slugify(name)}-{suffix}"


def random_price_enum():
    try:
        return PriceRangeEnum(random.randint(1, 4))
    except Exception:
        return None


def create_users(db, count=6):
    users = []
    for i in range(count):
        email = f"{fake.first_name().lower()}.{fake.last_name().lower()}@example.com"
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            users.append(existing)
            continue
        user = User(name=fake.name(), email=email, hashed_password="", )
        db.add(user)
        db.commit()
        db.refresh(user)
        users.append(user)
    return users


def run(num_restaurants: int = 50, num_reviews: int = 200):
    db = SessionLocal()
    try:
        users = create_users(db, count=8)

        restaurants = []
        for i in range(num_restaurants):
            name = f"{fake.last_name()} {fake.word().title()}"
            slug = make_slug(name, i + 1)
            existing = db.query(Restaurant).filter(Restaurant.slug == slug).first()
            if existing:
                restaurants.append(existing)
                continue

            rest = Restaurant(
                name=name,
                slug=slug,
                cuisine_type=", ".join(fake.words(nb=random.randint(1, 3))).title(),
                address=fake.street_address(),
                city=fake.city(),
                state=fake.state_abbr(),
                zip_code=fake.postcode(),
                country="US",
                phone=fake.phone_number(),
                website=fake.url(),
                description=fake.sentence(nb_words=18),
                price_range=random_price_enum(),
                latitude=float(fake.latitude()),
                longitude=float(fake.longitude()),
            )
            db.add(rest)
            db.flush()

            # Add 1-4 photos using picsum placeholders
            for _ in range(random.randint(1, 4)):
                photo_url = f"https://picsum.photos/seed/{slug}/{400 + random.randint(0,200)}/300"
                print(photo_url)
                db.add(RestaurantPhoto(restaurant_id=rest.id, file_path=photo_url))

            # Add simple hours (Mon-Sun open 11:00-22:00 with some closed days)
            for idx, d in enumerate(list(DayOfWeekEnum)):
                is_closed = random.random() < 0.05
                if is_closed:
                    oh = RestaurantHours(restaurant_id=rest.id, day_of_week=d, is_closed=True)
                else:
                    oh = RestaurantHours(
                        restaurant_id=rest.id,
                        day_of_week=d,
                        is_closed=False,
                        open_time=parse_time_str("11:00"),
                        close_time=parse_time_str("22:00"),
                    )
                db.add(oh)

            db.commit()
            db.refresh(rest)
            restaurants.append(rest)

        # Create reviews
        for _ in range(num_reviews):
            restaurant = random.choice(restaurants)
            user = random.choice(users)

            # Skip if this user already has a review for this restaurant (unique constraint)
            existing_review = (
                db.query(Review)
                .filter(Review.business_id == restaurant.id, Review.user_id == user.id)
                .first()
            )
            if existing_review:
                continue

            rating = random.randint(1, 5)
            body = fake.paragraph(nb_sentences=random.randint(1, 4))
            visited = date.today() - timedelta(days=random.randint(0, 800))
            review = Review(
                business_id=restaurant.id,
                user_id=user.id,
                rating=rating,
                title=fake.sentence(nb_words=6),
                body=body,
                visited_at=visited,
            )
            db.add(review)

            # occasionally add a review photo as a RestaurantPhoto (re-uses same table)
            if random.random() < 0.12:
                purl = f"https://picsum.photos/seed/rev{random.randint(1,10000)}/640/480"
                db.add(RestaurantPhoto(restaurant_id=restaurant.id, file_path=purl))

        db.commit()

        # Recalc ratings if project has helper (best-effort)
        try:
            from app.services.restaurant_service import recalculate_restaurant_ratings
            for r in restaurants:
                recalculate_restaurant_ratings(db, r.id)
        except Exception:
            pass

        print(f"Seeded {len(users)} users, {len(restaurants)} restaurants, {num_reviews} reviews")
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--restaurants", type=int, default=50)
    p.add_argument("--reviews", type=int, default=200)
    args = p.parse_args()
    run(num_restaurants=args.restaurants, num_reviews=args.reviews)
