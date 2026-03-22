from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func as sql_func
from typing import List
from database import get_db
from models.user import User
from models.restaurant import Restaurant
from models.review import Review
from schemas.restaurant import RestaurantOut
from schemas.review import ReviewOut
from auth.dependencies import get_current_user

router = APIRouter(prefix="/owner", tags=["Restaurant Owner"])


def _require_owner(user: User):
    if user.role != "owner":
        raise HTTPException(status_code=403, detail="Owner access required")


@router.get("/dashboard")
def get_owner_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_owner(current_user)

    restaurants = db.query(Restaurant).filter(Restaurant.owner_id == current_user.id).all()
    restaurant_ids = [r.id for r in restaurants]

    if not restaurant_ids:
        return {
            "total_restaurants": 0,
            "total_reviews": 0,
            "average_rating": None,
            "ratings_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
            "recent_reviews": [],
        }

    total_reviews = db.query(sql_func.count(Review.id)).filter(
        Review.restaurant_id.in_(restaurant_ids)
    ).scalar()

    avg_rating = db.query(sql_func.avg(Review.rating)).filter(
        Review.restaurant_id.in_(restaurant_ids)
    ).scalar()

    distribution = {}
    for star in range(1, 6):
        count = db.query(sql_func.count(Review.id)).filter(
            Review.restaurant_id.in_(restaurant_ids),
            Review.rating == star,
        ).scalar()
        distribution[star] = count

    recent_reviews = (
        db.query(Review)
        .filter(Review.restaurant_id.in_(restaurant_ids))
        .order_by(Review.created_at.desc())
        .limit(5)
        .all()
    )

    recent_out = []
    for review in recent_reviews:
        user = db.query(User).filter(User.id == review.user_id).first()
        restaurant = db.query(Restaurant).filter(Restaurant.id == review.restaurant_id).first()
        recent_out.append({
            "id": review.id,
            "user_name": user.name if user else None,
            "restaurant_name": restaurant.name if restaurant else None,
            "rating": review.rating,
            "comment": review.comment,
            "created_at": str(review.created_at) if review.created_at else None,
        })

    return {
        "total_restaurants": len(restaurants),
        "total_reviews": total_reviews,
        "average_rating": round(float(avg_rating), 1) if avg_rating else None,
        "ratings_distribution": distribution,
        "recent_reviews": recent_out,
    }


@router.get("/restaurants", response_model=List[RestaurantOut])
def get_owner_restaurants(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_owner(current_user)
    restaurants = db.query(Restaurant).filter(Restaurant.owner_id == current_user.id).all()
    result = []
    for r in restaurants:
        stats = db.query(
            sql_func.avg(Review.rating).label("avg_rating"),
            sql_func.count(Review.id).label("review_count"),
        ).filter(Review.restaurant_id == r.id).first()

        result.append(RestaurantOut(
            id=r.id, owner_id=r.owner_id, created_by=r.created_by,
            name=r.name, cuisine_type=r.cuisine_type, description=r.description,
            address=r.address, city=r.city, zip_code=r.zip_code,
            contact_info=r.contact_info, hours=r.hours, pricing_tier=r.pricing_tier,
            amenities=r.amenities, photos=r.photos, is_claimed=r.is_claimed,
            avg_rating=round(float(stats.avg_rating), 1) if stats.avg_rating else None,
            review_count=stats.review_count or 0,
            created_at=r.created_at,
        ))
    return result


@router.post("/claim/{restaurant_id}")
def claim_restaurant(
    restaurant_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_owner(current_user)

    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    if restaurant.is_claimed:
        raise HTTPException(status_code=409, detail="Restaurant is already claimed")

    restaurant.owner_id = current_user.id
    restaurant.is_claimed = True
    db.commit()
    return {"message": "Restaurant claimed successfully"}


@router.get("/restaurants/{restaurant_id}/reviews")
def get_owner_restaurant_reviews(
    restaurant_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_owner(current_user)

    restaurant = db.query(Restaurant).filter(
        Restaurant.id == restaurant_id,
        Restaurant.owner_id == current_user.id,
    ).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found or not owned by you")

    reviews = (
        db.query(Review)
        .filter(Review.restaurant_id == restaurant_id)
        .order_by(Review.created_at.desc())
        .all()
    )

    result = []
    for review in reviews:
        user = db.query(User).filter(User.id == review.user_id).first()
        result.append({
            "id": review.id,
            "user_name": user.name if user else None,
            "rating": review.rating,
            "comment": review.comment,
            "photos": review.photos,
            "created_at": str(review.created_at) if review.created_at else None,
        })
    return result
