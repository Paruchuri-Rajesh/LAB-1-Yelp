from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.auth import LoginRequest, SignupRequest
from app.schemas.user import UserWithToken
from app.services.auth_service import verify_password, create_access_token
from app.services.user_service import get_user_by_email, create_user

router = APIRouter()


@router.post("/signup", response_model=UserWithToken, status_code=status.HTTP_201_CREATED)
def signup(data: SignupRequest, db: Session = Depends(get_db)):
    if get_user_by_email(db, data.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )
    user = create_user(db, data)
    token = create_access_token(user.id)
    return UserWithToken(user=user, access_token=token)


@router.post("/login", response_model=UserWithToken)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = get_user_by_email(db, data.email)
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated.",
        )
    token = create_access_token(user.id)
    return UserWithToken(user=user, access_token=token)
