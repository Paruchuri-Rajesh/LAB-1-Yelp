"""
Seed or refresh restaurant data from the Yelp Fusion API.

Usage:
    export YELP_API_KEY=your_key_here
    python -m seeds.seed_yelp --location "Union City, CA" --term "restaurants" --limit 25
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.services.yelp_sync_service import upsert_from_yelp, YelpSyncError


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--location", default="Union City, CA")
    parser.add_argument("--term", default="restaurants")
    parser.add_argument("--limit", type=int, default=25)
    args = parser.parse_args()

    db = SessionLocal()
    try:
        loc = args.location.strip().lower()
        # Support a convenient 'bay-area' keyword which will iterate through
        # common Bay Area cities and fetch restaurants from each until the
        # requested total `limit` is reached.
        if loc in ("bay-area", "bay area", "bayarea", "bay"):
            cities = [
                "San Francisco, CA",
                "Oakland, CA",
                "Berkeley, CA",
                "San Jose, CA",
                "Palo Alto, CA",
                "Redwood City, CA",
                "Fremont, CA",
                "Hayward, CA",
                "Daly City, CA",
                "South San Francisco, CA",
            ]
            remaining = args.limit
            total_summary = {"imported": 0, "updated": 0, "reviews_imported": 0, "places_found": 0}
            for city in cities:
                if remaining <= 0:
                    break
                per_city = min(50, remaining)
                try:
                    summary = upsert_from_yelp(db, location=city, term=args.term, limit=per_city)
                    print(f"Seeded {city}:", summary)
                    total_summary["imported"] += summary.get("imported", 0)
                    total_summary["updated"] += summary.get("updated", 0)
                    total_summary["reviews_imported"] += summary.get("reviews_imported", 0)
                    total_summary["places_found"] += summary.get("places_found", 0)
                    remaining -= per_city
                except YelpSyncError as exc:
                    print(f"Yelp sync error for {city}: {exc}")
            print("Total summary:", total_summary)
        else:
            summary = upsert_from_yelp(db, location=args.location, term=args.term, limit=args.limit)
            print(summary)
    except YelpSyncError as exc:
        print(exc)
    finally:
        db.close()
