from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models.user import User
from models.restaurant import Restaurant
from models.favorite import Favorite
from schemas.favorite import FavoriteOut
from auth.dependencies import get_current_user

router = APIRouter(prefix="/favorites", tags=["Favorites"])


@router.post("/{restaurant_id}", response_model=FavoriteOut, status_code=status.HTTP_201_CREATED)
def add_favorite(
    restaurant_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    existing = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.restaurant_id == restaurant_id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Already in favorites")

    fav = Favorite(user_id=current_user.id, restaurant_id=restaurant_id)
    db.add(fav)
    db.commit()
    db.refresh(fav)

    return FavoriteOut(
        id=fav.id,
        user_id=fav.user_id,
        restaurant_id=fav.restaurant_id,
        restaurant_name=restaurant.name,
        restaurant_cuisine=restaurant.cuisine_type,
        restaurant_city=restaurant.city,
        created_at=fav.created_at,
    )


@router.delete("/{restaurant_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_favorite(
    restaurant_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    fav = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.restaurant_id == restaurant_id,
    ).first()
    if not fav:
        raise HTTPException(status_code=404, detail="Not in favorites")
    db.delete(fav)
    db.commit()


@router.get("", response_model=List[FavoriteOut])
def get_favorites(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    favorites = db.query(Favorite).filter(Favorite.user_id == current_user.id).all()
    result = []
    for fav in favorites:
        restaurant = db.query(Restaurant).filter(Restaurant.id == fav.restaurant_id).first()
        result.append(FavoriteOut(
            id=fav.id,
            user_id=fav.user_id,
            restaurant_id=fav.restaurant_id,
            restaurant_name=restaurant.name if restaurant else None,
            restaurant_cuisine=restaurant.cuisine_type if restaurant else None,
            restaurant_city=restaurant.city if restaurant else None,
            created_at=fav.created_at,
        ))
    return result


@router.get("/{restaurant_id}/status")
def check_favorite_status(
    restaurant_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    fav = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.restaurant_id == restaurant_id,
    ).first()
    return {"is_favorited": fav is not None}
