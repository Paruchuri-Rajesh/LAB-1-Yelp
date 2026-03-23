from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewUpdate, ReviewRead, ReviewsResponse
from app.services.review_service import (
    get_reviews_for_restaurant,
    create_review,
    update_review,
    delete_review,
)
import math
from fastapi import UploadFile, File
from app.services import file_service
from app.models.review import ReviewPhoto

router = APIRouter()


@router.get("/{restaurant_id}/reviews", response_model=ReviewsResponse)
def list_reviews(
    restaurant_id: int,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    items, total = get_reviews_for_restaurant(db, restaurant_id, page, page_size)
    return ReviewsResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


@router.post("/{restaurant_id}/reviews", response_model=ReviewRead, status_code=status.HTTP_201_CREATED)
def post_review(
    restaurant_id: int,
    data: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_review(db, restaurant_id, current_user.id, data, author_name=current_user.name)


@router.put("/{restaurant_id}/reviews/{review_id}", response_model=ReviewRead)
def edit_review(
    restaurant_id: int,
    review_id: int,
    data: ReviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return update_review(db, review_id, current_user.id, data)


@router.delete("/{restaurant_id}/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_review(
    restaurant_id: int,
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    delete_review(db, review_id, current_user.id)


@router.post("/{restaurant_id}/reviews/{review_id}/photos", status_code=status.HTTP_201_CREATED)
async def upload_review_photos(
    restaurant_id: int,
    review_id: int,
    photos: list[UploadFile] | None = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # ensure review exists and belongs to current_user
    from app.models.review import Review

    review = db.query(Review).filter(Review.id == review_id, Review.business_id == restaurant_id).first()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    if review.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to modify this review")

    added = 0
    if photos:
        for f in photos:
            path = await file_service.save_upload(f, "review_photos")
            rp = ReviewPhoto(review_id=review_id, file_path=path)
            db.add(rp)
            added += 1
        db.commit()
    return {"added": added}
