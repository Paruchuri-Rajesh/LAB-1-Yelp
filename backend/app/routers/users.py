from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
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
