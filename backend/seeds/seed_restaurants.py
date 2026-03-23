"""
Seed script — run from the backend/ directory:
    python -m seeds.seed_restaurants

Idempotent: checks for existing slugs/emails before inserting.
"""
import json
import sys
from datetime import datetime, time, date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from slugify import slugify
from app.database import SessionLocal, Base
from app.config import settings
from app.models.user import User, UserPreference
from app.models.restaurant import Restaurant, RestaurantHours, RestaurantPhoto
from app.models.review import Review
from app.models.enums import DayOfWeekEnum, PriceRangeEnum, SortPreferenceEnum
from app.services.auth_service import hash_password
from app.services.restaurant_service import recalculate_restaurant_ratings

DATA_DIR = Path(__file__).parent / "data"

SEED_USERS = [
    {"name": "Alice Chen",   "email": "alice@example.com",  "password": "password123"},
    {"name": "Bob Martinez", "email": "bob@example.com",    "password": "password123"},
    {"name": "Carol Smith",  "email": "carol@example.com",  "password": "password123"},
    {"name": "David Kim",    "email": "david@example.com",  "password": "password123"},
    {"name": "Eve Johnson",  "email": "eve@example.com",    "password": "password123"},
]

# Hard-coded reviews: list of (restaurant_index, user_index, rating, title, body)
SEED_REVIEWS = [
    (0,  0, 5, "Best pasta in SF",         "Incredible fresh pasta and the tiramisu is to die for. Will be coming back regularly."),
    (0,  1, 4, "Great atmosphere",          "Cozy and romantic. The carbonara was perfect, wine list could be bigger."),
    (0,  2, 5, "Authentic Italian",         "Reminds me of my trip to Naples. Genuine flavors, friendly staff."),
    (1,  1, 4, "Solid Tex-Mex",            "Fish tacos are every bit as good as advertised. Salsa bar is impressive."),
    (1,  3, 5, "Best tacos in Austin",      "A local institution. The al pastor is out of this world. Go on a weekend for mariachi."),
    (1,  4, 3, "Decent but crowded",        "Good food but the wait times on Friday nights are brutal. Come early."),
    (2,  0, 5, "Mind-blowing omakase",      "Chef Tanaka is a genius. Every bite was a revelation. Worth every penny."),
    (2,  2, 5, "A truly special experience","Save this for a very special occasion. The uni nigiri alone is worth the trip."),
    (3,  1, 4, "Excellent vegetarian menu", "The dosas are crispy and the sambar is rich. Butter chicken also top notch."),
    (3,  4, 5, "My go-to Indian spot",      "Consistent quality, generous portions, and the mango lassi is the best I have had."),
    (4,  0, 4, "Dim sum weekend tradition", "The har gow and siu mai are excellent. Can get very busy Sunday mornings — arrive early."),
    (4,  3, 5, "Old-school SF gem",         "Been coming here for 20 years. Quality never drops. Get the BBQ pork buns."),
    (5,  2, 4, "No-nonsense burgers",       "Exactly what a burger should be — juicy, messy, and delicious. Fries are phenomenal."),
    (5,  0, 3, "Good but nothing special",  "Solid burger but nothing that distinguishes it from other spots in Austin."),
    (6,  1, 5, "Pad thai perfection",       "Found my new favourite Thai spot. The pad see ew is also a must."),
    (6,  4, 4, "Authentic and fresh",       "Great quality ingredients. The papaya salad has a real kick to it."),
    (7,  2, 5, "Magical rooftop dinner",    "The rooftop view of Manhattan is stunning. Mezze platter was generous and delicious."),
    (7,  3, 4, "Wonderful mezze",           "Loved the hummus and grilled octopus. Service was a bit slow but attentive."),
    (8,  0, 5, "Perfect fine dining",       "Impeccable service, flawless food. The duck confit is the best I have eaten."),
    (9,  1, 4, "Taco Town delivers",        "Love the concept. Great variety and the sofritas are a solid vegan option."),
    (10, 2, 5, "Korean BBQ done right",     "The AUCE deal on Tuesdays is ridiculous value. Galbi is phenomenal."),
    (11, 3, 4, "Comforting pho",            "Rich broth, fresh herbs, quality beef. Exactly what you want on a cold day."),
    (12, 4, 5, "The definitive steakhouse", "Ribeye was the best steak I have ever had. The creamed spinach is a must-order side."),
    (13, 0, 4, "Deep dish debate settled",  "Had both styles side by side. The deep dish wins for me. Great fun."),
    (14, 1, 5, "Best brunch café in SF",    "The almond croissant and croque madame are spectacular. Staff are so welcoming."),
    (15, 2, 4, "Halal and delicious",       "Great to find quality halal food in Austin. The mixed grill platter is huge."),
    (16, 3, 5, "Best vegan spot in NYC",    "Incredible that 100% plant-based food can taste this good. The grain bowls are filling."),
    (17, 4, 4, "Sichuan heat lovers, rejoice", "Finally authentic spice levels. The mapo tofu numbs you in the best way."),
    (18, 0, 5, "Ramen therapy",             "The tonkotsu broth is insanely rich. Get there early — they do sell out."),
    (19, 1, 5, "Texas BBQ pilgrimage",      "Drove 45 minutes just for the brisket. Worth every mile. Cash only, bring cash."),
    (20, 2, 4, "Falafel that converts meat-eaters", "Best falafel I have ever had. The homemade hot sauce is addictive."),
    (21, 3, 5, "Biryani revelation",        "The 45-spice biryani is extraordinary. Every mouthful is complex and fragrant."),
    (22, 4, 4, "Thai fusion done right",    "The seafood tom kha is bowl-licking good. Mango sticky rice is perfect."),
    (23, 0, 5, "Nonna knows best",          "Sunday supper feels like being at someone's Italian grandmother's house. Magical."),
    (24, 1, 4, "Quick lunch hero",          "Reliably good and fast. The sweet and sour pork is exactly what the reviews say."),
]


def parse_time(t_str: str) -> time:
    h, m = t_str.split(":")
    return time(int(h), int(m))


def make_slug(name: str, suffix: int) -> str:
    return f"{slugify(name)}-{suffix}"


def run():
    db = SessionLocal()
    try:
        # ── Seed users ─────────────────────────────────────────────
        users = []
        for u in SEED_USERS:
            existing = db.query(User).filter(User.email == u["email"]).first()
            if existing:
                users.append(existing)
                print(f"  User exists: {u['email']}")
            else:
                user = User(
                    name=u["name"],
                    email=u["email"],
                    hashed_password=hash_password(u["password"]),
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                users.append(user)
                print(f"  Created user: {u['email']}")

        # ── Load restaurant data ────────────────────────────────────
        with open(DATA_DIR / "restaurants.json", encoding="utf-8") as f:
            restaurant_data = json.load(f)

        restaurants = []
        for idx, r in enumerate(restaurant_data):
            slug = make_slug(r["name"], idx + 1)
            existing = db.query(Restaurant).filter(Restaurant.slug == slug).first()
            if existing:
                restaurants.append(existing)
                print(f"  Restaurant exists: {r['name']}")
                continue

            rest = Restaurant(
                name=r["name"],
                slug=slug,
                cuisine_type=r.get("cuisine_type"),
                address=r.get("address"),
                city=r.get("city"),
                state=r.get("state"),
                zip_code=r.get("zip_code"),
                country=r.get("country"),
                phone=r.get("phone"),
                website=r.get("website") or None,
                description=r.get("description"),
                price_range=r.get("price_range"),
                latitude=r.get("latitude"),
                longitude=r.get("longitude"),
            )
            db.add(rest)
            db.flush()  # get ID

            # Hours
            day_map = {d.value: d for d in DayOfWeekEnum}
            for day_name, schedule in r.get("hours", {}).items():
                day_enum = day_map.get(day_name)
                if not day_enum:
                    continue
                closed = schedule.get("closed", False)
                hours = RestaurantHours(
                    restaurant_id=rest.id,
                    day_of_week=day_enum,
                    is_closed=closed,
                    open_time=parse_time(schedule["open"]) if not closed and "open" in schedule else None,
                    close_time=parse_time(schedule["close"]) if not closed and "close" in schedule else None,
                )
                db.add(hours)

            db.commit()
            db.refresh(rest)
            restaurants.append(rest)
            print(f"  Created restaurant: {r['name']}")

        # ── Seed reviews ───────────────────────────────────────────
        for rest_idx, user_idx, rating, title, body in SEED_REVIEWS:
            if rest_idx >= len(restaurants) or user_idx >= len(users):
                continue
            restaurant = restaurants[rest_idx]
            user = users[user_idx]

            existing_review = (
                db.query(Review)
                .filter(
                    Review.business_id == restaurant.id,
                    Review.user_id == user.id,
                )
                .first()
            )
            if existing_review:
                continue

            review = Review(
                business_id=restaurant.id,
                user_id=user.id,
                rating=rating,
                title=title,
                body=body,
                visited_at=date(2025, 12, 1),
            )
            db.add(review)

        db.commit()

        # ── Recalculate ratings ─────────────────────────────────────
        for restaurant in restaurants:
            recalculate_restaurant_ratings(db, restaurant.id)

        print("\nSeeding complete!")
        print(f"  {len(users)} users")
        print(f"  {len(restaurants)} restaurants")
        print(f"  {len(SEED_REVIEWS)} reviews")

    finally:
        db.close()


if __name__ == "__main__":
    run()
