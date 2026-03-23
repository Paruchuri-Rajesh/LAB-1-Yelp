from app.schemas.auth import TokenResponse, LoginRequest, SignupRequest
from app.schemas.user import UserRead, UserUpdate, UserWithToken
from app.schemas.preferences import PreferencesRead, PreferencesUpdate
from app.schemas.restaurant import (
    RestaurantListItem,
    RestaurantDetail,
    RestaurantSearchResponse,
    HoursRead,
    PhotoRead,
)
from app.schemas.review import ReviewCreate, ReviewUpdate, ReviewRead, ReviewsResponse

__all__ = [
    "TokenResponse", "LoginRequest", "SignupRequest",
    "UserRead", "UserUpdate", "UserWithToken",
    "PreferencesRead", "PreferencesUpdate",
    "RestaurantListItem", "RestaurantDetail", "RestaurantSearchResponse",
    "ReviewCreate", "ReviewUpdate", "ReviewRead", "ReviewsResponse",
]
