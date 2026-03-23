from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
import math
from app.database import get_db
from app.schemas.restaurant import (
    RestaurantDetail,
    RestaurantSearchResponse,
    RestaurantListItem,
    RestaurantPlaceItem,
    RestaurantImportRequest,
    RestaurantImportResponse,
)
from app.dependencies import get_optional_current_user
from app.models.restaurant import Favorite
from app.services.restaurant_service import (
    search_restaurants,
    get_restaurant_by_id,
    search_places,
    record_restaurant_view,
    parse_address_components,
    geocode_address,
)
from app.services.restaurant_service import parse_address_components
from app.dependencies import get_current_user
from app.models.user import User
from fastapi import File, Form, UploadFile
from app.services import file_service
from app.models.restaurant import RestaurantPhoto, Restaurant
from app.services.review_service import create_review
from app.schemas.review import ReviewCreate
from datetime import date
from app.services.yelp_sync_service import upsert_from_yelp, YelpSyncError

router = APIRouter()


@router.get("/places", response_model=list[RestaurantPlaceItem])
def places(
    q: Optional[str] = None,
    limit: int = 8,
    db: Session = Depends(get_db),
):
    return search_places(db, q=q, limit=limit)


@router.post("/import/yelp", response_model=RestaurantImportResponse)
def import_from_yelp(
    data: RestaurantImportRequest,
    db: Session = Depends(get_db),
):
    try:
        return upsert_from_yelp(db, location=data.location, term=data.term, limit=data.limit)
    except YelpSyncError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Yelp sync failed: {exc}")


@router.get("", response_model=RestaurantSearchResponse)
def search(
    q: Optional[str] = None,
    cuisine: Optional[str] = None,
    location: Optional[str] = None,
    city: Optional[str] = None,
    price_range: Optional[str] = None,
    min_rating: Optional[float] = None,
    sort_by: str = "recommended",
    page: int = 1,
    page_size: int = 20,
    open_now: bool | None = None,
    has_reservations: bool | None = None,
    offers_delivery: bool | None = None,
    offers_takeout: bool | None = None,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    items, total = search_restaurants(
        db,
        q=q,
        cuisine=cuisine,
        location=location,
        city=city,
        price_range=price_range,
        min_rating=min_rating,
        sort_by=sort_by,
        page=page,
        page_size=page_size,
        open_now=open_now,
        has_reservations=has_reservations,
        offers_delivery=offers_delivery,
        offers_takeout=offers_takeout,
    )
    list_items = [
        RestaurantListItem(
            id=r.id,
            name=r.name,
            slug=r.slug,
            cuisine_type=r.cuisine_type,
            city=r.city,
            state=r.state,
            address=r.address,
            zip_code=r.zip_code,
            price_range=r.price_range,
            avg_rating=r.avg_rating,
            review_count=r.review_count,
            primary_photo=r.primary_photo,
            latitude=r.latitude,
            longitude=r.longitude,
            source=r.source,
            is_favorited=False,
        )
        for r in items
    ]

    # If there's a current user, annotate favorites in bulk
    if current_user and list_items:
        try:
            rest_ids = [r.id for r in items]
            fav_rows = db.query(Favorite.restaurant_id).filter(Favorite.user_id == current_user.id, Favorite.restaurant_id.in_(rest_ids)).all()
            fav_ids = {row[0] for row in fav_rows}
            for li in list_items:
                if li.id in fav_ids:
                    li.is_favorited = True
        except Exception:
            # don't fail search if favorites lookup fails
            pass
    return RestaurantSearchResponse(
        items=list_items,
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


@router.get("/{restaurant_id}", response_model=RestaurantDetail)
def get_restaurant(restaurant_id: int, db: Session = Depends(get_db)):
    restaurant = get_restaurant_by_id(db, restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found.")
    record_restaurant_view(db, restaurant_id)
    return restaurant



@router.post("/suggest", response_model=RestaurantDetail, status_code=201)
async def suggest_restaurant(
    name: str = Form(...),
    address: str | None = Form(None),
    city: str | None = Form(None),
    state: str | None = Form(None),
    zip_code: str | None = Form(None),
    phone: str | None = Form(None),
    website: str | None = Form(None),
    cuisine_type: str | None = Form(None),
    price_range: str | None = Form(None),
    description: str | None = Form(None),
    photos: list[UploadFile] | None = File(None),
    # optional review fields
    rating: int | None = Form(None),
    title: str | None = Form(None),
    body: str | None = Form(None),
    visited_at: date | None = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # attempt to derive city/state/zip from the address if not explicitly provided
    if not city or not state:
        street, parsed_city, parsed_state, parsed_zip = parse_address_components(address)
        city = city or parsed_city
        state = state or parsed_state
        zip_code = zip_code or parsed_zip

    # try to geocode address to get lat/lon for map placement
    lat, lon = geocode_address(address or f"{city or ''} {state or ''}")

    # create restaurant as a suggested/local entry
    rest = Restaurant(
        name=name,
        address=address,
        city=city,
        state=state,
        zip_code=zip_code,
        phone=phone,
        website=website,
        cuisine_type=cuisine_type,
        price_range=price_range,
        description=description,
        source="suggested",
        latitude=lat,
        longitude=lon,
    )
    db.add(rest)
    db.commit()
    db.refresh(rest)

    # save photos if any
    if photos:
        for idx, f in enumerate(photos):
            path = await file_service.save_upload(f, "restaurant_photos")
            photo = RestaurantPhoto(restaurant_id=rest.id, file_path=path, is_primary=(idx == 0))
            db.add(photo)
        db.commit()

    # optional: create an initial review by the suggesting user if rating provided
    if rating is not None:
        # build ReviewCreate and call service
        review_payload = ReviewCreate(rating=rating, title=title, body=body, visited_at=visited_at)
        create_review(db, rest.id, current_user.id, review_payload, author_name=current_user.name)

    return get_restaurant_by_id(db, rest.id)
