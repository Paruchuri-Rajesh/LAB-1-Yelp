from pydantic import BaseModel
from app.schemas.restaurant import RestaurantListItem, RestaurantDetail
from app.schemas.review import ReviewRead


class OwnerDashboardSummary(BaseModel):
    total_restaurants: int
    total_views: int
    total_reviews: int
    avg_rating: float
    recent_reviews: list[ReviewRead]
    restaurants: list[RestaurantListItem]


class OwnerRestaurantDashboard(BaseModel):
    restaurant: RestaurantDetail
    total_views: int
    total_reviews: int
    avg_rating: float
    recent_reviews: list[ReviewRead]
    rating_breakdown: dict[str, int]
