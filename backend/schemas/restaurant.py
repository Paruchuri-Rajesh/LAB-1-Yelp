from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class RestaurantCreate(BaseModel):
    name: str
    cuisine_type: str
    address: str
    city: str
    zip_code: Optional[str] = None
    contact_info: Optional[str] = None
    description: Optional[str] = None
    hours: Optional[dict] = None
    pricing_tier: Optional[str] = None
    amenities: Optional[List[str]] = None


class RestaurantUpdate(BaseModel):
    name: Optional[str] = None
    cuisine_type: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    zip_code: Optional[str] = None
    contact_info: Optional[str] = None
    description: Optional[str] = None
    hours: Optional[dict] = None
    pricing_tier: Optional[str] = None
    amenities: Optional[List[str]] = None


class RestaurantOut(BaseModel):
    id: int
    owner_id: Optional[int] = None
    created_by: Optional[int] = None
    name: str
    cuisine_type: str
    description: Optional[str] = None
    address: str
    city: str
    zip_code: Optional[str] = None
    contact_info: Optional[str] = None
    hours: Optional[dict] = None
    pricing_tier: Optional[str] = None
    amenities: Optional[List[str]] = None
    photos: Optional[List[str]] = None
    is_claimed: bool = False
    avg_rating: Optional[float] = None
    review_count: int = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
