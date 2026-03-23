from sqlalchemy.orm import Session
from app.models.user import User, OwnerProfile
from app.schemas.auth import SignupRequest
from app.schemas.user import UserUpdate
from app.services.auth_service import get_password_hash as hash_password


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
