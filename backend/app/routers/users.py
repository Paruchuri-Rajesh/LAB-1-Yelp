from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import UserRead, UserUpdate
from app.schemas.review import ReviewRead, ReviewsResponse
from app.services.user_service import update_user, set_avatar, remove_avatar
from app.services.file_service import save_profile_picture, delete_file
from app.services.review_service import get_user_reviews
import math

router = APIRouter()


@router.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserRead)
def update_me(
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return update_user(db, current_user, data)


@router.post("/me/avatar", response_model=UserRead)
async def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    old_path = current_user.profile_picture_path
    relative_path = await save_profile_picture(file)
    user = set_avatar(db, current_user, relative_path)
    if old_path:
        delete_file(old_path)
    return user


@router.delete("/me/avatar", response_model=UserRead)
def delete_avatar(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    old_path = current_user.profile_picture_path
    user = remove_avatar(db, current_user)
    if old_path:
        delete_file(old_path)
    return user


@router.get("/me/reviews", response_model=ReviewsResponse)
def my_reviews(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items, total = get_user_reviews(db, current_user.id, page, page_size)
    return ReviewsResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


@router.post("/me/favorites/{restaurant_id}", status_code=204)
def favorite_restaurant(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.services.user_service import add_favorite
    try:
        add_favorite(db, current_user, int(restaurant_id))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/me/favorites/{restaurant_id}", status_code=204)
def unfavorite_restaurant(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.services.user_service import remove_favorite
    remove_favorite(db, current_user, int(restaurant_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me/favorites")
def my_favorites(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.services.user_service import list_favorites
    from app.schemas.restaurant import RestaurantSearchResponse, RestaurantListItem

    items, total = list_favorites(db, current_user, page, page_size)
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
        )
        for r in items
    ]
    return {
        "items": [it.model_dump() if hasattr(it, 'model_dump') else it.dict() for it in list_items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total // page_size + (1 if total % page_size else 0)) if total else 0,
    }
