from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
from app.models.review import Review
from app.schemas.review import ReviewCreate, ReviewUpdate
from app.services.restaurant_service import recalculate_restaurant_ratings
from app.models.user import User


def get_reviews_for_restaurant(
    db: Session,
    restaurant_id: int,
    page: int = 1,
    page_size: int = 20,
):
    query = (
        db.query(Review)
        .options(joinedload(Review.user), joinedload(Review.photos), joinedload(Review.restaurant))
        .filter(Review.business_id == restaurant_id)
        .order_by(Review.created_at.desc())
    )
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def get_user_reviews(db: Session, user_id: int, page: int = 1, page_size: int = 20):
    # Primary: reviews explicitly tied to the user_id
    query = (
        db.query(Review)
        .options(joinedload(Review.user), joinedload(Review.photos), joinedload(Review.restaurant))
        .filter(Review.user_id == user_id)
        .order_by(Review.created_at.desc())
    )
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    # Fallback: some reviews (from imports or seeders) may not have user_id set
    # but do have author_name populated. If the user has no tied reviews, try
    # to find reviews whose author_name matches the current user's name
    # (case-insensitive, partial match).
    if total == 0:
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.name:
            author_query = (
                db.query(Review)
                .options(joinedload(Review.user), joinedload(Review.photos), joinedload(Review.restaurant))
                .filter(Review.author_name.ilike(f"%{user.name}%"))
                .order_by(Review.created_at.desc())
            )
            total = author_query.count()
            items = author_query.offset((page - 1) * page_size).limit(page_size).all()

    return items, total


def create_review(
    db: Session,
    restaurant_id: int,
    user_id: int,
    data: ReviewCreate,
    author_name: str | None = None,
) -> Review:
    # prevent users with owner accounts from posting reviews at all
    user = db.query(User).filter(User.id == user_id).first()
    if user and getattr(user, 'is_owner', False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account owners are not allowed to post reviews.")
    # additionally prevent restaurant owners (ownership claim) from reviewing their own restaurant
    from app.models.restaurant import RestaurantOwnership
    owner_row = db.query(RestaurantOwnership).filter(
        RestaurantOwnership.restaurant_id == restaurant_id,
        RestaurantOwnership.owner_id == user_id,
    ).first()
    if owner_row:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owners cannot review their own restaurant.")
    existing = (
        db.query(Review)
        .filter(Review.business_id == restaurant_id, Review.user_id == user_id)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already reviewed this restaurant.",
        )
    review = Review(
        business_id=restaurant_id,
        user_id=user_id,
        author_name=author_name,
        source="local",
        **data.model_dump(),
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    recalculate_restaurant_ratings(db, restaurant_id)
    return db.query(Review).options(joinedload(Review.user), joinedload(Review.photos)).filter(Review.id == review.id).first()


def update_review(
    db: Session,
    review_id: int,
    user_id: int,
    data: ReviewUpdate,
) -> Review:
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found.")
    if review.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized.")
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(review, field, value)
    db.commit()
    db.refresh(review)
    recalculate_restaurant_ratings(db, review.business_id)
    return db.query(Review).options(joinedload(Review.user), joinedload(Review.photos)).filter(Review.id == review.id).first()


def delete_review(db: Session, review_id: int, user_id: int):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found.")
    if review.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized.")
    restaurant_id = review.business_id
    db.delete(review)
    db.commit()
    recalculate_restaurant_ratings(db, restaurant_id)
