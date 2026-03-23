from sqlalchemy.orm import Session
from app.models.user import User, OwnerProfile
from app.schemas.auth import SignupRequest
from app.schemas.user import UserUpdate
from app.services.auth_service import get_password_hash as hash_password
from app.models.restaurant import Favorite, Restaurant
from app.models.user import User


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, data: SignupRequest) -> User:
    user = User(
        name=data.name,
        email=data.email,
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    db.flush()

    if data.account_type == "owner":
        db.add(
            OwnerProfile(
                user_id=user.id,
                business_name=data.business_name,
                restaurant_location=data.restaurant_location,
            )
        )

    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user: User, data: UserUpdate) -> User:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


def set_avatar(db: Session, user: User, relative_path: str) -> User:
    user.profile_picture_path = relative_path
    db.commit()
    db.refresh(user)
    return user


def remove_avatar(db: Session, user: User) -> User:
    user.profile_picture_path = None
    db.commit()
    db.refresh(user)
    return user


def add_favorite(db: Session, user: User, restaurant_id: int) -> None:
    # ensure restaurant exists
    rest = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not rest:
        raise ValueError("Restaurant not found")
    exists = db.query(Favorite).filter(Favorite.user_id == user.id, Favorite.restaurant_id == restaurant_id).first()
    if exists:
        return
    fav = Favorite(user_id=user.id, restaurant_id=restaurant_id)
    db.add(fav)
    db.commit()


def remove_favorite(db: Session, user: User, restaurant_id: int) -> None:
    fav = db.query(Favorite).filter(Favorite.user_id == user.id, Favorite.restaurant_id == restaurant_id).first()
    if not fav:
        return
    db.delete(fav)
    db.commit()


def list_favorites(db: Session, user: User, page: int = 1, page_size: int = 20):
    q = db.query(Restaurant).join(Favorite, Favorite.restaurant_id == Restaurant.id).filter(Favorite.user_id == user.id, Restaurant.is_closed == False)
    total = q.count()
    items = q.order_by(Favorite.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return items, total
