import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func as sql_func
from typing import List, Optional
from database import get_db
from models.user import User
from models.restaurant import Restaurant
from models.review import Review
from schemas.restaurant import RestaurantCreate, RestaurantUpdate, RestaurantOut
from auth.dependencies import get_current_user
from config import UPLOAD_DIR

router = APIRouter(prefix="/restaurants", tags=["Restaurants"])


def _build_restaurant_out(restaurant: Restaurant, db: Session) -> RestaurantOut:
    stats = db.query(
        sql_func.avg(Review.rating).label("avg_rating"),
        sql_func.count(Review.id).label("review_count"),
    ).filter(Review.restaurant_id == restaurant.id).first()

    return RestaurantOut(
        id=restaurant.id,
        owner_id=restaurant.owner_id,
        created_by=restaurant.created_by,
        name=restaurant.name,
        cuisine_type=restaurant.cuisine_type,
        description=restaurant.description,
        address=restaurant.address,
        city=restaurant.city,
        zip_code=restaurant.zip_code,
        contact_info=restaurant.contact_info,
        hours=restaurant.hours,
        pricing_tier=restaurant.pricing_tier,
        amenities=restaurant.amenities,
        photos=restaurant.photos,
        is_claimed=restaurant.is_claimed,
        avg_rating=round(float(stats.avg_rating), 1) if stats.avg_rating else None,
        review_count=stats.review_count or 0,
        created_at=restaurant.created_at,
    )


@router.post("", response_model=RestaurantOut, status_code=status.HTTP_201_CREATED)
def create_restaurant(
    data: RestaurantCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    restaurant = Restaurant(
        name=data.name,
        cuisine_type=data.cuisine_type,
        address=data.address,
        city=data.city,
        zip_code=data.zip_code,
        contact_info=data.contact_info,
        description=data.description,
        hours=data.hours,
        pricing_tier=data.pricing_tier,
        amenities=data.amenities,
        created_by=current_user.id,
        owner_id=current_user.id if current_user.role == "owner" else None,
        is_claimed=current_user.role == "owner",
    )
    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)
    return _build_restaurant_out(restaurant, db)


@router.get("", response_model=List[RestaurantOut])
def search_restaurants(
    name: Optional[str] = Query(None),
    cuisine_type: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    zip_code: Optional[str] = Query(None),
    pricing_tier: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Restaurant)

    if name:
        query = query.filter(Restaurant.name.ilike(f"%{name}%"))
    if cuisine_type:
        query = query.filter(Restaurant.cuisine_type.ilike(f"%{cuisine_type}%"))
    if city:
        query = query.filter(Restaurant.city.ilike(f"%{city}%"))
    if zip_code:
        query = query.filter(Restaurant.zip_code == zip_code)
    if pricing_tier:
        query = query.filter(Restaurant.pricing_tier == pricing_tier)
    if keyword:
        keyword_filter = f"%{keyword}%"
        query = query.filter(
            (Restaurant.name.ilike(keyword_filter))
            | (Restaurant.description.ilike(keyword_filter))
            | (Restaurant.cuisine_type.ilike(keyword_filter))
        )

    restaurants = query.offset(skip).limit(limit).all()
    return [_build_restaurant_out(r, db) for r in restaurants]


@router.get("/{restaurant_id}", response_model=RestaurantOut)
def get_restaurant(restaurant_id: int, db: Session = Depends(get_db)):
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return _build_restaurant_out(restaurant, db)


@router.put("/{restaurant_id}", response_model=RestaurantOut)
def update_restaurant(
    restaurant_id: int,
    data: RestaurantUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    if restaurant.owner_id != current_user.id and restaurant.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this restaurant")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(restaurant, key, value)
    db.commit()
    db.refresh(restaurant)
    return _build_restaurant_out(restaurant, db)


@router.post("/{restaurant_id}/photos", response_model=RestaurantOut)
async def upload_restaurant_photos(
    restaurant_id: int,
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    photo_urls = restaurant.photos or []
    for file in files:
        ext = os.path.splitext(file.filename)[1]
        filename = f"{restaurant_id}_{uuid.uuid4().hex}{ext}"
        filepath = os.path.join(UPLOAD_DIR, "restaurants", filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "wb") as f:
            content = await file.read()
            f.write(content)
        photo_urls.append(f"/uploads/restaurants/{filename}")

    restaurant.photos = photo_urls
    db.commit()
    db.refresh(restaurant)
    return _build_restaurant_out(restaurant, db)
