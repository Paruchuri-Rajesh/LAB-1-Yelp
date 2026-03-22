"""Seed script to populate the database with 100 sample restaurants and reviews."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database import SessionLocal, engine, Base
from models.user import User
from models.restaurant import Restaurant
from models.review import Review
from utils.password import hash_password
import random
import json

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# Create sample users
sample_users = [
    {"name": "Alice Johnson", "email": "alice@example.com", "role": "user"},
    {"name": "Bob Smith", "email": "bob@example.com", "role": "user"},
    {"name": "Carol Davis", "email": "carol@example.com", "role": "user"},
    {"name": "David Lee", "email": "david@example.com", "role": "user"},
    {"name": "Emma Wilson", "email": "emma@example.com", "role": "user"},
    {"name": "Frank Brown", "email": "frank@example.com", "role": "owner"},
    {"name": "Grace Kim", "email": "grace@example.com", "role": "owner"},
    {"name": "Henry Park", "email": "henry@example.com", "role": "owner"},
]

users = []
for u in sample_users:
    existing = db.query(User).filter(User.email == u["email"]).first()
    if not existing:
        user = User(name=u["name"], email=u["email"], password_hash=hash_password("password123"), role=u["role"])
        db.add(user)
        db.flush()
        users.append(user)
    else:
        users.append(existing)

db.commit()
print(f"Created/found {len(users)} users")

# Restaurant data
cuisines = ["Italian", "Chinese", "Mexican", "Indian", "Japanese", "American", "Thai", "French", "Korean", "Mediterranean"]
price_tiers = ["$", "$$", "$$$", "$$$$"]
cities_data = [
    ("San Jose", "CA", "95112"), ("San Francisco", "CA", "94102"), ("Los Angeles", "CA", "90001"),
    ("New York", "NY", "10001"), ("Chicago", "IL", "60601"), ("Austin", "TX", "73301"),
    ("Seattle", "WA", "98101"), ("Portland", "OR", "97201"), ("Denver", "CO", "80201"),
    ("Miami", "FL", "33101"), ("Boston", "MA", "02101"), ("Nashville", "TN", "37201"),
    ("Santa Clara", "CA", "95050"), ("Sunnyvale", "CA", "94085"), ("Mountain View", "CA", "94040"),
    ("Palo Alto", "CA", "94301"), ("Cupertino", "CA", "95014"), ("Fremont", "CA", "94536"),
    ("Oakland", "CA", "94601"), ("Berkeley", "CA", "94701"),
]

amenities_pool = ["WiFi", "Outdoor Seating", "Parking", "Live Music", "Happy Hour", "Delivery",
                   "Takeout", "Reservations", "Full Bar", "TV", "Pet Friendly", "Wheelchair Accessible"]

restaurants_data = [
    # Italian
    ("Pasta Paradise", "Italian", "Authentic Italian pasta and wood-fired pizzas in a cozy setting"),
    ("Trattoria Roma", "Italian", "Traditional Roman cuisine with handmade pasta and fine wines"),
    ("Bella Napoli", "Italian", "Neapolitan-style pizzeria with imported ingredients from Italy"),
    ("Il Giardino", "Italian", "Garden dining with classic Italian dishes and homemade gelato"),
    ("Vino e Pasta", "Italian", "Wine bar and pasta house featuring regional Italian specialties"),
    ("La Dolce Vita", "Italian", "Upscale Italian dining with a romantic ambiance"),
    ("Mangia Bene", "Italian", "Family-style Italian restaurant with generous portions"),
    ("Osteria del Sol", "Italian", "Sun-drenched patio serving rustic Italian fare"),
    ("Primo Piatto", "Italian", "Modern Italian cuisine with seasonal tasting menus"),
    ("Casa di Pizza", "Italian", "Casual pizzeria with craft beers and classic pies"),
    # Chinese
    ("Golden Dragon", "Chinese", "Cantonese and Szechuan dishes in an elegant setting"),
    ("Jade Palace", "Chinese", "Dim sum brunch and authentic Chinese banquet dinners"),
    ("Wok & Roll", "Chinese", "Fast-casual Chinese stir-fry with customizable bowls"),
    ("Shanghai Garden", "Chinese", "Shanghai-style cuisine with soup dumplings and noodles"),
    ("Lucky Bamboo", "Chinese", "Traditional Chinese comfort food with family recipes"),
    ("Dragon Pearl", "Chinese", "Upscale Chinese dining with Peking duck and seafood"),
    ("Ming Dynasty", "Chinese", "Imperial Chinese cuisine in a grand dining room"),
    ("Panda Express Gourmet", "Chinese", "Elevated Chinese-American favorites"),
    ("Tea Garden", "Chinese", "Chinese tea house with dim sum and small plates"),
    ("Szechuan Fire", "Chinese", "Bold and spicy Szechuan specialties"),
    # Mexican
    ("El Mexicano", "Mexican", "Authentic Mexican street food and handmade tortillas"),
    ("Casa Oaxaca", "Mexican", "Oaxacan mole and traditional Mexican cooking"),
    ("Taco Fiesta", "Mexican", "Vibrant taqueria with creative taco combinations"),
    ("La Cocina", "Mexican", "Home-style Mexican cooking with fresh salsas"),
    ("Cantina del Sol", "Mexican", "Lively cantina with margaritas and Mexican plates"),
    ("Burrito Bandido", "Mexican", "Mission-style burritos and Mexican bowls"),
    ("Puebla Kitchen", "Mexican", "Puebla-inspired dishes with rich mole sauces"),
    ("Mariscos del Mar", "Mexican", "Mexican seafood specialties and ceviche bar"),
    ("Agave Grill", "Mexican", "Grilled meats and agave-based cocktails"),
    ("Tortilleria Fresca", "Mexican", "Fresh tortillas made daily with traditional fillings"),
    # Indian
    ("Taj Mahal", "Indian", "North Indian cuisine with tandoori specialties and rich curries"),
    ("Spice Route", "Indian", "Pan-Indian flavors from Kerala to Punjab"),
    ("Curry House", "Indian", "Classic Indian curries and fresh naan bread"),
    ("Bollywood Bites", "Indian", "Vibrant Indian street food and chaat"),
    ("Saffron Kitchen", "Indian", "Fine dining Indian restaurant with saffron-infused dishes"),
    ("Masala Magic", "Indian", "South Indian dosas and North Indian thalis"),
    ("Tandoori Nights", "Indian", "Late-night tandoori grill with live music"),
    ("Chai & Chutney", "Indian", "Casual Indian cafe with chai and snacks"),
    ("Biryani House", "Indian", "Hyderabadi biryani and Mughlai cuisine"),
    ("Namaste India", "Indian", "Warm and welcoming Indian family restaurant"),
    # Japanese
    ("Sakura Sushi", "Japanese", "Fresh sushi and sashimi with omakase options"),
    ("Ramen House", "Japanese", "Rich tonkotsu and miso ramen bowls"),
    ("Tokyo Grill", "Japanese", "Teppanyaki and Japanese BBQ experience"),
    ("Zen Garden", "Japanese", "Minimalist Japanese dining with kaiseki courses"),
    ("Sushi Express", "Japanese", "Conveyor belt sushi with daily fresh fish"),
    ("Izakaya Yuki", "Japanese", "Japanese pub food with sake and beer"),
    ("Udon Master", "Japanese", "Handmade udon noodles in traditional broths"),
    ("Tempura Ten", "Japanese", "Light and crispy tempura with dipping sauces"),
    ("Matcha House", "Japanese", "Japanese desserts and matcha beverages"),
    ("Yakitori Lane", "Japanese", "Charcoal-grilled chicken skewers and Japanese bites"),
    # American
    ("The Burger Joint", "American", "Gourmet burgers with hand-cut fries and milkshakes"),
    ("BBQ Smokehouse", "American", "Slow-smoked BBQ meats with Southern sides"),
    ("Liberty Diner", "American", "Classic American diner with all-day breakfast"),
    ("Steak & Co", "American", "Premium steaks and craft cocktails"),
    ("Farm Table", "American", "Farm-to-table American cuisine with local ingredients"),
    ("Blue Plate Special", "American", "Comfort food classics in a retro setting"),
    ("The Grill Room", "American", "Upscale American grill with seasonal menu"),
    ("Mac & Cheese Factory", "American", "Creative mac and cheese variations"),
    ("Wing House", "American", "Buffalo wings with 20 sauce options"),
    ("Pancake Palace", "American", "Breakfast spot with fluffy pancakes and waffles"),
    # Thai
    ("Thai Orchid", "Thai", "Authentic Thai curries and stir-fries"),
    ("Bangkok Street", "Thai", "Thai street food favorites and pad thai"),
    ("Basil & Lime", "Thai", "Modern Thai cuisine with fresh herbs"),
    ("Coconut Kitchen", "Thai", "Coconut-based Thai curries and rice dishes"),
    ("Spicy Lemongrass", "Thai", "Bold Thai flavors with lemongrass and chili"),
    # French
    ("Bistro Paris", "French", "Classic French bistro with wine and cheese"),
    ("Le Petit Chef", "French", "French fine dining with prix fixe menus"),
    ("Cafe Montmartre", "French", "Parisian-style cafe with crepes and pastries"),
    ("Boulangerie", "French", "French bakery and cafe with fresh bread daily"),
    ("Chateau Rouge", "French", "French country cooking with rustic charm"),
    # Korean
    ("Seoul Kitchen", "Korean", "Korean BBQ with premium marinated meats"),
    ("Kimchi House", "Korean", "Traditional Korean dishes with homemade kimchi"),
    ("Bibimbap Bowl", "Korean", "Build-your-own bibimbap with fresh toppings"),
    ("K-Town Grill", "Korean", "Korean BBQ and fried chicken"),
    ("Tofu Village", "Korean", "Korean soft tofu stew and hot pot"),
    # Mediterranean
    ("Olive & Vine", "Mediterranean", "Mediterranean tapas and olive oil tastings"),
    ("Aegean Table", "Mediterranean", "Greek and Turkish Mediterranean cuisine"),
    ("Hummus Bar", "Mediterranean", "Fresh hummus, falafel, and pita"),
    ("Med Grill", "Mediterranean", "Grilled meats and seafood Mediterranean style"),
    ("Fig & Feta", "Mediterranean", "Mediterranean salads, wraps, and mezze"),
    # Extra variety
    ("Pho Saigon", "Thai", "Vietnamese-Thai fusion with pho and noodle soups"),
    ("Crepe Studio", "French", "Sweet and savory crepes with artisan fillings"),
    ("Noodle Bar", "Japanese", "Japanese and Asian noodle soups"),
    ("Taco Truck Kitchen", "Mexican", "Elevated food truck tacos in a brick-and-mortar"),
    ("Curry & Kabob", "Indian", "Indian-Pakistani grill with fresh kabobs"),
    ("Pizza Roma", "Italian", "Thin-crust Roman-style pizza by the slice"),
    ("Dim Sum Palace", "Chinese", "Weekend dim sum brunch with 50+ options"),
    ("Burger & Brew", "American", "Craft burgers paired with local craft beers"),
    ("Sushi Zen", "Japanese", "High-end sushi bar with seasonal omakase"),
    ("Taqueria Los Amigos", "Mexican", "Neighborhood taqueria with homestyle cooking"),
]

hours_templates = [
    {"monday": "11:00 AM - 9:00 PM", "tuesday": "11:00 AM - 9:00 PM", "wednesday": "11:00 AM - 9:00 PM",
     "thursday": "11:00 AM - 10:00 PM", "friday": "11:00 AM - 11:00 PM", "saturday": "10:00 AM - 11:00 PM", "sunday": "10:00 AM - 9:00 PM"},
    {"monday": "8:00 AM - 10:00 PM", "tuesday": "8:00 AM - 10:00 PM", "wednesday": "8:00 AM - 10:00 PM",
     "thursday": "8:00 AM - 10:00 PM", "friday": "8:00 AM - 11:00 PM", "saturday": "9:00 AM - 11:00 PM", "sunday": "9:00 AM - 9:00 PM"},
    {"monday": "12:00 PM - 10:00 PM", "tuesday": "12:00 PM - 10:00 PM", "wednesday": "12:00 PM - 10:00 PM",
     "thursday": "12:00 PM - 10:00 PM", "friday": "12:00 PM - 11:30 PM", "saturday": "11:00 AM - 11:30 PM", "sunday": "11:00 AM - 9:30 PM"},
]

addresses = [
    "123 Main St", "456 Oak Ave", "789 Elm Blvd", "321 Pine Rd", "654 Maple Dr",
    "111 First St", "222 Second Ave", "333 Third Blvd", "444 Fourth Rd", "555 Fifth Dr",
    "100 Market St", "200 Broadway", "300 Park Ave", "400 Center St", "500 University Ave",
    "600 Castro St", "700 Valencia St", "800 Mission St", "900 Howard St", "1000 Folsom St",
]

contacts = [
    "(408) 555-{:04d}", "(415) 555-{:04d}", "(213) 555-{:04d}",
    "(212) 555-{:04d}", "(312) 555-{:04d}", "(512) 555-{:04d}",
    "(206) 555-{:04d}", "(503) 555-{:04d}", "(303) 555-{:04d}",
    "(305) 555-{:04d}",
]

review_comments = [
    "Amazing food and great atmosphere! Will definitely come back.",
    "The service was excellent and the food was delicious.",
    "Good portions and reasonable prices. Highly recommend.",
    "One of the best restaurants in the area. Love it!",
    "Solid food, nice ambiance. A bit pricey but worth it.",
    "Fantastic experience from start to finish. 10/10 would recommend.",
    "The flavors were incredible. Authentic and well-prepared.",
    "Decent food but the wait time was a bit long.",
    "Great spot for a date night. Romantic and cozy.",
    "Family-friendly with a kids menu. Everyone enjoyed their meal.",
    "The chef really knows what they're doing. Outstanding dishes.",
    "Came here for lunch and was pleasantly surprised. Quick and tasty.",
    "Not bad, but I've had better. Average experience overall.",
    "Loved the appetizers! The main course was good too.",
    "Perfect for a casual dinner with friends. Fun atmosphere.",
    "The cocktails were as good as the food. Great bar selection.",
    "Fresh ingredients and creative menu. Will be a regular.",
    "Friendly staff and quick service. The food hits the spot.",
    "A hidden gem! Can't believe I didn't know about this place sooner.",
    "The desserts are to die for. Save room for the tiramisu!",
]

# Create 100 restaurants
created_count = 0
existing_count = db.query(Restaurant).count()
if existing_count >= 100:
    print(f"Already have {existing_count} restaurants. Skipping restaurant creation.")
else:
    for i, (name, cuisine, desc) in enumerate(restaurants_data):
        existing = db.query(Restaurant).filter(Restaurant.name == name).first()
        if existing:
            continue

        city, state, zip_code = random.choice(cities_data)
        address = random.choice(addresses)
        contact = random.choice(contacts).format(random.randint(1000, 9999))
        price = random.choice(price_tiers)
        hours = random.choice(hours_templates)
        num_amenities = random.randint(2, 6)
        rest_amenities = random.sample(amenities_pool, num_amenities)

        owner = random.choice([u for u in users if u.role == "owner"]) if random.random() > 0.6 else None
        creator = random.choice(users)

        restaurant = Restaurant(
            name=name,
            cuisine_type=cuisine,
            description=desc,
            address=f"{address}",
            city=city,
            zip_code=zip_code,
            contact_info=contact,
            hours=hours,
            pricing_tier=price,
            amenities=rest_amenities,
            photos=None,
            owner_id=owner.id if owner else None,
            created_by=creator.id,
            is_claimed=owner is not None,
        )
        db.add(restaurant)
        created_count += 1

    db.commit()
    print(f"Created {created_count} restaurants")

# Create sample reviews
all_restaurants = db.query(Restaurant).all()
review_users = [u for u in users if u.role == "user"]
reviews_created = 0

for restaurant in all_restaurants:
    existing_reviews = db.query(Review).filter(Review.restaurant_id == restaurant.id).count()
    if existing_reviews > 0:
        continue

    num_reviews = random.randint(2, 8)
    reviewers = random.sample(review_users, min(num_reviews, len(review_users)))

    for reviewer in reviewers:
        existing = db.query(Review).filter(
            Review.user_id == reviewer.id,
            Review.restaurant_id == restaurant.id
        ).first()
        if existing:
            continue

        rating = random.choices([3, 4, 5, 2, 1], weights=[25, 35, 25, 10, 5])[0]
        comment = random.choice(review_comments)

        review = Review(
            user_id=reviewer.id,
            restaurant_id=restaurant.id,
            rating=rating,
            comment=comment,
        )
        db.add(review)
        reviews_created += 1

db.commit()
print(f"Created {reviews_created} reviews")
print("Seed complete!")
db.close()
