from collections import Counter
from math import ceil, cos, radians
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_, cast, String, distinct
from fastapi import HTTPException, status
from app.models.restaurant import Restaurant, RestaurantOwnership, RestaurantView
from app.models.review import Review
import requests
from urllib.parse import urlencode


def _restaurant_base_query(db: Session):
    return db.query(Restaurant).options(joinedload(Restaurant.photos), joinedload(Restaurant.hours)).filter(Restaurant.is_closed == False)


def parse_address_components(address: str) -> tuple[str | None, str | None, str | None]:
    """Simple heuristic parser to extract (street, city, state_zip) components from a free-form address.

    Returns (street, city, state_zip_or_state, zip_code) depending on what it can find.
    """
    if not address:
        return None, None, None
    parts = [p.strip() for p in address.split(',') if p.strip()]
    street = None
    city = None
    state = None
    zip_code = None
    if len(parts) >= 3:
        street = ', '.join(parts[:-2])
        city = parts[-2]
        last = parts[-1]
    elif len(parts) == 2:
        street = parts[0]
        city = parts[1]
        last = ''
    else:
        # single part -- nothing to parse use as street
        street = parts[0]
        last = ''

    if last:
        tokens = last.split()
        if len(tokens) >= 1:
            state = tokens[0]
        if len(tokens) >= 2:
            maybe_zip = tokens[-1]
            if maybe_zip.replace('-', '').isdigit():
                zip_code = maybe_zip

    return street, city, state, zip_code


def geocode_address(address: str) -> tuple[float | None, float | None]:
    """Try to geocode an address using Nominatim (OpenStreetMap). Returns (lat, lon) or (None, None)."""
    if not address:
        return None, None
    try:
        params = {'q': address, 'format': 'json', 'limit': 1}
        url = f"https://nominatim.openstreetmap.org/search?{urlencode(params)}"
        headers = {'User-Agent': 'sjsu-classroom-app/1.0 (you@domain.example)'}
        resp = requests.get(url, headers=headers, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list) and data:
            lat = float(data[0].get('lat'))
            lon = float(data[0].get('lon'))
            return lat, lon
    except Exception:
        # geocoding is best-effort; ignore failures
        return None, None
    return None, None


def search_restaurants(
    db: Session,
    q: str | None = None,
    cuisine: str | None = None,
    location: str | None = None,
    city: str | None = None,
    price_range: str | None = None,
    min_rating: float | None = None,
    sort_by: str = "recommended",
    page: int = 1,
    page_size: int = 20,
    open_now: bool | None = None,
    has_reservations: bool | None = None,
    offers_delivery: bool | None = None,
    offers_takeout: bool | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_miles: float | None = None,
):
    query = _restaurant_base_query(db)

    if q:
        like_pattern = f"%{q}%"
        query = query.filter(
            or_(
                Restaurant.name.ilike(like_pattern),
                Restaurant.cuisine_type.ilike(like_pattern),
                Restaurant.description.ilike(like_pattern),
                Restaurant.address.ilike(like_pattern),
                Restaurant.city.ilike(like_pattern),
            )
        )
    if cuisine:
        query = query.filter(Restaurant.cuisine_type.ilike(f"%{cuisine}%"))
    if location:
        like_pattern = f"%{location}%"
        # Include suggested restaurants even if they don't have matching city/state/zip/address
        # so user-suggested entries are discoverable immediately after creation.
        query = query.filter(
            or_(
                Restaurant.city.ilike(like_pattern),
                Restaurant.state.ilike(like_pattern),
                Restaurant.zip_code.ilike(like_pattern),
                Restaurant.address.ilike(like_pattern),
                Restaurant.source == 'suggested',
            )
        )
    if city:
        query = query.filter(Restaurant.city.ilike(f"%{city}%"))
    if price_range:
        query = query.filter(Restaurant.price_range == price_range)

    if latitude is not None and longitude is not None and radius_miles:
        try:
            lat_delta = float(radius_miles) / 69.0
            lon_divisor = max(abs(cos(radians(float(latitude)))), 0.1)
            lon_delta = float(radius_miles) / (69.0 * lon_divisor)
            query = query.filter(Restaurant.latitude.isnot(None), Restaurant.longitude.isnot(None))
            query = query.filter(Restaurant.latitude >= float(latitude) - lat_delta)
            query = query.filter(Restaurant.latitude <= float(latitude) + lat_delta)
            query = query.filter(Restaurant.longitude >= float(longitude) - lon_delta)
            query = query.filter(Restaurant.longitude <= float(longitude) + lon_delta)
        except Exception:
            pass
    if min_rating is not None:
        query = query.filter(Restaurant.avg_rating >= min_rating)

    # boolean filters
    if offers_delivery:
        # transactions is stored as a comma-separated string like 'delivery,pickup'
        query = query.filter(Restaurant.transactions.ilike('%delivery%'))
    if offers_takeout:
        # some sources label takeout as 'takeout' or 'pickup'
        query = query.filter(
            or_(
                Restaurant.transactions.ilike('%takeout%'),
                Restaurant.transactions.ilike('%pickup%'),
            )
        )
    if has_reservations:
        query = query.filter(Restaurant.transactions.ilike('%restaurant_reservation%'))
    if open_now:
        # best-effort: filter restaurants that have today's hours and are not closed
        from datetime import datetime
        from app.models.restaurant import RestaurantHours

        day_name = datetime.now().strftime('%A').lower()
        # join with hours and require an open record where is_closed is False and current time between open and close
        now_time = datetime.now().time()
        query = query.join(Restaurant.hours).filter(
            Restaurant.hours.any(
                RestaurantHours.day_of_week == day_name,
            )
        )

    sort_map = {
        "recommended": (Restaurant.avg_rating.desc(), Restaurant.review_count.desc(), Restaurant.name.asc()),
        "rating": (Restaurant.avg_rating.desc(), Restaurant.review_count.desc()),
        "review_count": (Restaurant.review_count.desc(), Restaurant.avg_rating.desc()),
        "name": (Restaurant.name.asc(),),
        "price": (Restaurant.price_range.asc(), Restaurant.avg_rating.desc()),
        "newest": (Restaurant.created_at.desc(),),
    }
    query = query.order_by(*sort_map.get(sort_by, sort_map["recommended"]))

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def search_places(db: Session, q: str | None = None, limit: int = 8):
    query = (
        db.query(Restaurant.city, Restaurant.state, Restaurant.zip_code)
        .filter(Restaurant.is_closed == False)
        .filter(Restaurant.city.isnot(None))
    )
    if q:
        like_pattern = f"%{q}%"
        query = query.filter(
            or_(
                Restaurant.city.ilike(like_pattern),
                Restaurant.state.ilike(like_pattern),
                Restaurant.zip_code.ilike(like_pattern),
            )
        )
    rows = query.distinct().limit(limit).all()
    results = []
    for city, state, zip_code in rows:
        label = ", ".join([part for part in [city, state, zip_code] if part])
        results.append({"label": label, "city": city, "state": state, "zip_code": zip_code})
    return results


def get_restaurant_by_id(db: Session, restaurant_id: int) -> Restaurant | None:
    return (
        db.query(Restaurant)
        .options(joinedload(Restaurant.photos), joinedload(Restaurant.hours))
        .filter(Restaurant.id == restaurant_id, Restaurant.is_closed == False)
        .first()
    )


def record_restaurant_view(db: Session, restaurant_id: int, viewer_user_id: int | None = None):
    db.add(RestaurantView(restaurant_id=restaurant_id, viewer_user_id=viewer_user_id))
    db.commit()


def recalculate_restaurant_ratings(db: Session, restaurant_id: int):
    result = (
        db.query(
            func.avg(Review.rating).label("avg"),
            func.count(Review.id).label("cnt"),
        )
        .filter(Review.business_id == restaurant_id)
        .one()
    )
    db.query(Restaurant).filter(Restaurant.id == restaurant_id).update(
        {
            "avg_rating": round(float(result.avg or 0), 2),
            "review_count": int(result.cnt or 0),
        }
    )
    db.commit()


def claim_restaurant(db: Session, restaurant_id: int, owner_id: int):
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found.")

    claim = (
        db.query(RestaurantOwnership)
        .filter(RestaurantOwnership.restaurant_id == restaurant_id, RestaurantOwnership.owner_id == owner_id)
        .first()
    )
    if claim:
        return claim

    claim = RestaurantOwnership(restaurant_id=restaurant_id, owner_id=owner_id, status="claimed")
    db.add(claim)
    db.commit()
    db.refresh(claim)
    return claim


def get_owner_restaurants(db: Session, owner_id: int):
    restaurants = (
        db.query(Restaurant)
        .join(RestaurantOwnership, RestaurantOwnership.restaurant_id == Restaurant.id)
        .options(joinedload(Restaurant.photos))
        .filter(RestaurantOwnership.owner_id == owner_id)
        .order_by(Restaurant.name.asc())
        .all()
    )
    return restaurants


def ensure_owner_has_restaurant(db: Session, owner_id: int, restaurant_id: int) -> Restaurant:
    restaurant = (
        db.query(Restaurant)
        .join(RestaurantOwnership, RestaurantOwnership.restaurant_id == Restaurant.id)
        .options(joinedload(Restaurant.photos), joinedload(Restaurant.hours))
        .filter(Restaurant.id == restaurant_id, RestaurantOwnership.owner_id == owner_id)
        .first()
    )
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Owned restaurant not found.")
    return restaurant


def update_owned_restaurant(db: Session, owner_id: int, restaurant_id: int, data: dict):
    restaurant = ensure_owner_has_restaurant(db, owner_id, restaurant_id)
    # If any address-related fields are included, try to parse missing components
    # and perform a best-effort geocode to update latitude/longitude so map pins stay in sync.
    address_keys = {"address", "city", "state", "zip_code"}
    if any(k in data for k in address_keys):
        # Determine current / incoming values
        incoming_address = data.get("address") if data.get("address") is not None else restaurant.address
        incoming_city = data.get("city") if data.get("city") is not None else restaurant.city
        incoming_state = data.get("state") if data.get("state") is not None else restaurant.state
        incoming_zip = data.get("zip_code") if data.get("zip_code") is not None else getattr(restaurant, "zip_code", None)

        # If city or state missing, try to parse from the free-form address
        if (not incoming_city or not incoming_state) and incoming_address:
            street, parsed_city, parsed_state, parsed_zip = parse_address_components(incoming_address)
            incoming_city = incoming_city or parsed_city
            incoming_state = incoming_state or parsed_state
            incoming_zip = incoming_zip or parsed_zip
            # write parsed back into data so it's persisted below
            if incoming_city:
                data["city"] = incoming_city
            if incoming_state:
                data["state"] = incoming_state
            if incoming_zip:
                data["zip_code"] = incoming_zip

        # Build an address string to geocode. Prefer explicit address, fall back to city/state/zip.
        geocode_input = incoming_address or " ".join([p for p in [incoming_city, incoming_state, incoming_zip] if p])
        lat, lon = geocode_address(geocode_input)
        # Only set latitude/longitude if geocoding returned something useful (best-effort)
        if lat is not None or lon is not None:
            data["latitude"] = lat
            data["longitude"] = lon

    for field, value in data.items():
        setattr(restaurant, field, value)
    db.commit()
    db.refresh(restaurant)
    return restaurant


def _views_count_for_restaurant(db: Session, restaurant_id: int) -> int:
    return int(db.query(func.count(RestaurantView.id)).filter(RestaurantView.restaurant_id == restaurant_id).scalar() or 0)


def get_owner_dashboard_summary(db: Session, owner_id: int):
    restaurants = get_owner_restaurants(db, owner_id)
    restaurant_ids = [r.id for r in restaurants]
    if not restaurant_ids:
        return {
            "total_restaurants": 0,
            "total_views": 0,
            "total_reviews": 0,
            "avg_rating": 0.0,
            "recent_reviews": [],
            "restaurants": [],
        }

    total_views = int(
        db.query(func.count(RestaurantView.id))
        .filter(RestaurantView.restaurant_id.in_(restaurant_ids))
        .scalar()
        or 0
    )
    total_reviews = int(sum(r.review_count or 0 for r in restaurants))
    avg_rating = round(sum((r.avg_rating or 0) for r in restaurants) / max(len(restaurants), 1), 2)
    recent_reviews = (
        db.query(Review)
        .options(joinedload(Review.user), joinedload(Review.photos))
        .filter(Review.business_id.in_(restaurant_ids))
        .order_by(Review.created_at.desc())
        .limit(5)
        .all()
    )
    return {
        "total_restaurants": len(restaurants),
        "total_views": total_views,
        "total_reviews": total_reviews,
        "avg_rating": avg_rating,
        "recent_reviews": recent_reviews,
        "restaurants": restaurants,
    }


def get_owner_restaurant_dashboard(db: Session, owner_id: int, restaurant_id: int):
    restaurant = ensure_owner_has_restaurant(db, owner_id, restaurant_id)
    reviews = (
        db.query(Review)
        .options(joinedload(Review.user), joinedload(Review.photos))
        .filter(Review.business_id == restaurant_id)
        .order_by(Review.created_at.desc())
        .all()
    )
    rating_breakdown = Counter(str(stars) for stars in range(1, 6))
    for review in reviews:
        if review.rating:
            rating_breakdown[str(review.rating)] += 1
    return {
        "restaurant": restaurant,
        "total_views": _views_count_for_restaurant(db, restaurant_id),
        "total_reviews": len(reviews),
        "avg_rating": round(float(restaurant.avg_rating or 0), 2),
        "recent_reviews": reviews[:8],
        "rating_breakdown": {str(i): rating_breakdown.get(str(i), 0) for i in range(5, 0, -1)},
    }
