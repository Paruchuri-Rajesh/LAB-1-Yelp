import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models.user import User
from models.restaurant import Restaurant
from models.review import Review
from schemas.review import ReviewCreate, ReviewUpdate, ReviewOut
from auth.dependencies import get_current_user
from config import UPLOAD_DIR

router = APIRouter(tags=["Reviews"])


def _build_review_out(review: Review, db: Session) -> ReviewOut:
    user = db.query(User).filter(User.id == review.user_id).first()
    restaurant = db.query(Restaurant).filter(Restaurant.id == review.restaurant_id).first()
    return ReviewOut(
        id=review.id,
        user_id=review.user_id,
        user_name=user.name if user else None,
        restaurant_id=review.restaurant_id,
        restaurant_name=restaurant.name if restaurant else None,
        rating=review.rating,
        comment=review.comment,
        photos=review.photos,
        created_at=review.created_at,
        updated_at=review.updated_at,
    )


@router.post("/reviews", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def create_review(
    data: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    restaurant = db.query(Restaurant).filter(Restaurant.id == data.restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    existing = db.query(Review).filter(
        Review.user_id == current_user.id,
        Review.restaurant_id == data.restaurant_id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="You have already reviewed this restaurant")

    if data.rating < 1 or data.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    review = Review(
        user_id=current_user.id,
        restaurant_id=data.restaurant_id,
        rating=data.rating,
        comment=data.comment,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return _build_review_out(review, db)


@router.get("/restaurants/{restaurant_id}/reviews", response_model=List[ReviewOut])
def get_restaurant_reviews(
    restaurant_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    reviews = (
        db.query(Review)
        .filter(Review.restaurant_id == restaurant_id)
        .order_by(Review.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [_build_review_out(r, db) for r in reviews]


@router.put("/reviews/{review_id}", response_model=ReviewOut)
def update_review(
    review_id: int,
    data: ReviewUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if review.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only edit your own reviews")

    update_data = data.model_dump(exclude_unset=True)
    if "rating" in update_data and (update_data["rating"] < 1 or update_data["rating"] > 5):
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    for key, value in update_data.items():
        setattr(review, key, value)
    db.commit()
    db.refresh(review)
    return _build_review_out(review, db)


@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(
    review_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if review.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own reviews")
    db.delete(review)
    db.commit()


@router.get("/users/reviews", response_model=List[ReviewOut])
def get_user_reviews(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    reviews = (
        db.query(Review)
        .filter(Review.user_id == current_user.id)
        .order_by(Review.created_at.desc())
        .all()
    )
    return [_build_review_out(r, db) for r in reviews]


@router.post("/reviews/{review_id}/photos", response_model=ReviewOut)
async def upload_review_photos(
    review_id: int,
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if review.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only edit your own reviews")

    photo_urls = review.photos or []
    for file in files:
        ext = os.path.splitext(file.filename)[1]
        filename = f"{review_id}_{uuid.uuid4().hex}{ext}"
        filepath = os.path.join(UPLOAD_DIR, "reviews", filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "wb") as f:
            content = await file.read()
            f.write(content)
        photo_urls.append(f"/uploads/reviews/{filename}")

    review.photos = photo_urls
    db.commit()
    db.refresh(review)
    return _build_review_out(review, db)
