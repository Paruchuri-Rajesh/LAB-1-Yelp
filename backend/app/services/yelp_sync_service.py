"""Yelp sync helpers.

This module provides utilities for syncing restaurants, hours, photos and
reviews from the Yelp Fusion API into the local database models.

Important note about reviews:
 - The Yelp Fusion Reviews endpoint (GET /v3/businesses/{id}/reviews)
     returns at most a small set of review snippets (currently up to 3).
     There is no supported parameter to page or increase that number. If you
     need the full set of reviews for a business you'll need to use a
     different source (Yelp's dataset downloads if available, a licensed feed,
     or an authorized scraping approach with respect to Yelp's Terms of Use).

 - The methods below will import whatever snippets the API provides and
     will log/skip businesses where reviews are not available (404/400).

Alternatives to get more reviews:
 - Use Yelp's dataset or business data products (commercial/licensed).
 - Implement a careful, terms-compliant scraper (not recommended unless you
     have permission). Scraping may also require rendering JavaScript and is
     more brittle.

This module documents these limitations to avoid confusion when only a few
reviews are imported per business.
"""

from __future__ import annotations
import os
from datetime import datetime
from typing import Any
import requests
from slugify import slugify
from sqlalchemy.orm import Session
from app.models.restaurant import Restaurant, RestaurantHours, RestaurantPhoto
from app.models.review import Review
from app.services.restaurant_service import recalculate_restaurant_ratings


YELP_SEARCH_URL = "https://api.yelp.com/v3/businesses/search"
YELP_BUSINESS_URL = "https://api.yelp.com/v3/businesses/{id}"
YELP_REVIEWS_URL = "https://api.yelp.com/v3/businesses/{id}/reviews"
DAY_NAMES = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


class YelpSyncError(Exception):
    pass


class YelpSyncService:
    def __init__(self, api_key: str | None = None):
        # Prefer explicit api_key argument, then environment variable. If not
        # present, fall back to application settings which will read `.env` via
        # pydantic settings when the app is configured. This allows CLI scripts
        # (like seeds) to pick up the key from backend/.env even when the
        # environment doesn't expose it.
        from app.config import settings

        self.api_key = api_key or os.environ.get("YELP_API_KEY") or getattr(settings, "YELP_API_KEY", None)
        if not self.api_key:
            raise YelpSyncError("Missing YELP_API_KEY environment variable.")
        self.headers = {"Authorization": f"Bearer {self.api_key}"}

    def _get(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        response = requests.get(url, headers=self.headers, params=params, timeout=20)
        response.raise_for_status()
        return response.json()

    def fetch_businesses(self, location: str, term: str = "restaurants", limit: int = 20) -> list[dict[str, Any]]:
        # Yelp search supports limit up to 50 and an offset for pagination.
        # Implement simple pagination to allow fetching more than 50 results when
        # the caller requests a larger `limit` (e.g., 100).
        results: list[dict[str, Any]] = []
        offset = 0
        remaining = int(limit)
        while remaining > 0:
            per_call = min(50, remaining)
            params = {"location": location, "term": term, "limit": per_call, "offset": offset}
            try:
                payload = self._get(YELP_SEARCH_URL, params)
            except requests.HTTPError as e:
                # If Yelp returns an error for a particular offset, stop and return
                # whatever we've collected so far.
                print(f"[Yelp] search error for {location} offset={offset}: {e}")
                break
            batch = payload.get("businesses", []) or []
            if not batch:
                break
            results.extend(batch)
            fetched = len(batch)
            remaining -= fetched
            offset += fetched
            # if Yelp returned fewer than requested, stop early
            if fetched < per_call:
                break
        return results

    def fetch_business_details(self, yelp_business_id: str) -> dict[str, Any]:
        return self._get(YELP_BUSINESS_URL.format(id=yelp_business_id))

    def fetch_business_reviews(self, yelp_business_id: str) -> list[dict]:
        """Fetch reviews for a business.

        Returns the review objects provided by Yelp Fusion. Note: the Yelp
        endpoint only exposes a small set of review snippets (currently up to
        3) and does not support pagination or a larger limit. This method will
        therefore return at most the reviews Yelp exposes via the API.

        The caller should treat the result as a best-effort import of
        available snippets; do not expect a complete historical review set.

        Error handling:
        - 404: no reviews endpoint found for the business -> returns []
        - 400: logs the response body and returns []
        - other HTTP errors are re-raised.
        """
        try:
            payload = self._get(YELP_REVIEWS_URL.format(id=yelp_business_id))
            return payload.get("reviews", []) or []
        except requests.HTTPError as e:
            status = e.response.status_code if e.response is not None else None

            if status == 404:
                print(f"[Yelp] Skipping reviews for {yelp_business_id}: 404 Not Found")
                return []

            if status == 400:
                try:
                    body = e.response.json()
                except Exception:
                    body = e.response.text
                print(f"[Yelp] Skipping reviews for {yelp_business_id}: {body}")
                return []

            raise


def _parse_time(value: str | None):
    if not value or len(value) != 4:
        return None
    try:
        return datetime.strptime(value, "%H%M").time()
    except ValueError:
        return None


def _upsert_hours(db: Session, restaurant_id: int, details: dict[str, Any]):
    db.query(RestaurantHours).filter(RestaurantHours.restaurant_id == restaurant_id).delete()
    hours_data = details.get("hours") or []
    if not hours_data:
        return
    for open_item in hours_data[0].get("open", []):
        day_index = open_item.get("day")
        day_name = DAY_NAMES[day_index] if isinstance(day_index, int) and 0 <= day_index < len(DAY_NAMES) else None
        if not day_name:
            continue
        db.add(
            RestaurantHours(
                restaurant_id=restaurant_id,
                day_of_week=day_name,
                open_time=_parse_time(open_item.get("start")),
                close_time=_parse_time(open_item.get("end")),
                is_closed=False,
            )
        )


def _upsert_photos(db: Session, restaurant_id: int, details: dict[str, Any], summary: dict[str, Any]):
    db.query(RestaurantPhoto).filter(RestaurantPhoto.restaurant_id == restaurant_id).delete()
    photo_urls = details.get("photos") or []
    if not photo_urls and summary.get("image_url"):
        photo_urls = [summary["image_url"]]
    for index, photo_url in enumerate(photo_urls):
        db.add(
            RestaurantPhoto(
                restaurant_id=restaurant_id,
                file_path=photo_url,
                is_primary=index == 0,
            )
        )


def _upsert_reviews(db: Session, restaurant: Restaurant, review_items: list[dict[str, Any]]):
    imported = 0
    for item in review_items:
        external_id = item.get("id")
        existing = db.query(Review).filter(Review.external_review_id == external_id).first()
        if existing:
            existing.rating = int(item.get("rating") or 0)
            existing.body = item.get("text")
            existing.author_name = (item.get("user") or {}).get("name")
            existing.author_image_url = (item.get("user") or {}).get("image_url")
            existing.source_url = item.get("url")
            date_str = item.get("time_created", "")[:10]
            existing.visited_at = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else None
            existing.source = "yelp"
            continue

        date_str = item.get("time_created", "")[:10]
        db.add(
            Review(
                business_id=restaurant.id,
                user_id=None,
                external_review_id=external_id,
                source="yelp",
                rating=int(item.get("rating") or 0),
                body=item.get("text"),
                author_name=(item.get("user") or {}).get("name"),
                author_image_url=(item.get("user") or {}).get("image_url"),
                source_url=item.get("url"),
                visited_at=datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else None,
            )
        )
        imported += 1
    return imported


def upsert_from_yelp(db: Session, location: str, term: str = "restaurants", limit: int = 20):
    service = YelpSyncService()
    businesses = service.fetch_businesses(location=location, term=term, limit=limit)
    imported = 0
    updated = 0
    reviews_imported = 0
    place_keys: set[tuple[str | None, str | None, str | None]] = set()

    for index, item in enumerate(businesses, start=1):
        yelp_id = item.get("id")
        if not yelp_id:
            continue

        try:
            details = service.fetch_business_details(yelp_id)
        except Exception as e:
            # If fetching details fails for a single business, log and skip it
            print(f"[Yelp] Skipping business details for {yelp_id}: {e}")
            continue

        try:
            reviews = service.fetch_business_reviews(yelp_id)
        except Exception as e:
            # Reviews may be missing or the reviews endpoint may error for some businesses.
            # Log and continue with an empty list of reviews for this business.
            print(f"[Yelp] Skipping reviews for {yelp_id}: {e}")
            reviews = []
        restaurant = db.query(Restaurant).filter(Restaurant.yelp_id == yelp_id).first()
        summary_categories = item.get("categories") or []
        detail_categories = details.get("categories") or summary_categories
        cuisine = ", ".join(c.get("title") for c in detail_categories if c.get("title")) or None
        slug_value = item.get("alias") or f"{slugify(item.get('name') or 'restaurant')}-{index}"

        # Build a richer description string using available fields from the
        # business details so the frontend "About this place" panel shows
        # meaningful information instead of a generic placeholder.
        categories_list = [c.get("title") for c in detail_categories if c.get("title")]
        categories_str = ", ".join(categories_list)

        desc_parts = []
        if details.get("description"):
            desc_parts.append(details.get("description"))
        if categories_str:
            desc_parts.append(categories_str)
        if details.get("transactions"):
            desc_parts.append("Offers: " + ", ".join(details.get("transactions")))
        if details.get("price"):
            desc_parts.append("Price: " + details.get("price"))
        if details.get("display_phone"):
            desc_parts.append("Phone: " + details.get("display_phone"))

        description_text = " — ".join(part for part in desc_parts if part)

        payload = {
            "yelp_id": yelp_id,
            "name": item.get("name"),
            "slug": slug_value,
            "cuisine_type": cuisine,
            "description": description_text or (details.get("special_hours") and "Imported from Yelp API" or "Imported from Yelp API"),
            "address": ", ".join((details.get("location") or item.get("location") or {}).get("display_address") or []) or None,
            "city": (details.get("location") or item.get("location") or {}).get("city"),
            "state": (details.get("location") or item.get("location") or {}).get("state") or (details.get("location") or item.get("location") or {}).get("state_code"),
            "zip_code": (details.get("location") or item.get("location") or {}).get("zip_code"),
            "country": (details.get("location") or item.get("location") or {}).get("country"),
            "latitude": (details.get("coordinates") or item.get("coordinates") or {}).get("latitude"),
            "longitude": (details.get("coordinates") or item.get("coordinates") or {}).get("longitude"),
            "phone": details.get("display_phone") or item.get("display_phone") or item.get("phone"),
            "website": details.get("url") or item.get("url"),
            "image_url": details.get("image_url") or item.get("image_url"),
            "yelp_url": details.get("url") or item.get("url"),
            "price_range": details.get("price") or item.get("price"),
            "avg_rating": float(details.get("rating") or item.get("rating") or 0),
            "review_count": int(details.get("review_count") or item.get("review_count") or 0),
            "is_closed": bool(details.get("is_closed") if details.get("is_closed") is not None else item.get("is_closed")),
            "transactions": ", ".join(details.get("transactions") or item.get("transactions") or []),
            "hours_raw": details.get("hours"),
            "amenities": [k for k, v in (details.get("attributes") or {}).items() if isinstance(v, bool) and v],
            "keywords": [c.get("alias") for c in detail_categories if c.get("alias")],
            "source": "yelp",
        }

        if restaurant:
            for key, value in payload.items():
                setattr(restaurant, key, value)
            updated += 1
        else:
            restaurant = Restaurant(**payload)
            db.add(restaurant)
            db.flush()
            imported += 1

        db.flush()
        _upsert_hours(db, restaurant.id, details)
        _upsert_photos(db, restaurant.id, details, item)
        reviews_imported += _upsert_reviews(db, restaurant, reviews)
        place_keys.add((restaurant.city, restaurant.state, restaurant.zip_code))

    db.commit()
    for business in businesses:
        rid = db.query(Restaurant.id).filter(Restaurant.yelp_id == business.get("id")).scalar()
        if rid:
            recalculate_restaurant_ratings(db, rid)

    return {
        "imported": imported,
        "updated": updated,
        "reviews_imported": reviews_imported,
        "places_found": len([item for item in place_keys if any(item)]),
        "message": "Yelp sync completed. Note: Yelp Fusion only exposes a small set of review snippets per business.",
    }
