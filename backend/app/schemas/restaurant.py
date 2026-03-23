from __future__ import annotations
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, time
from app.models.enums import PriceRangeEnum


class HoursRead(BaseModel):
    day_of_week: str
    open_time: Optional[time] = None
    close_time: Optional[time] = None
    is_closed: bool = False

    class Config:
        from_attributes = True


class PhotoRead(BaseModel):
    id: int
    file_path: str
    caption: Optional[str] = None
    is_primary: bool = False

    class Config:
        from_attributes = True


class RestaurantListItem(BaseModel):
    id: int
    name: str
    slug: Optional[str] = None
    cuisine_type: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    address: Optional[str] = None
    zip_code: Optional[str] = None
    price_range: Optional[str] = None
    avg_rating: float = 0.0
    review_count: int = 0
    primary_photo: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    source: str = "local"
    is_favorited: bool = False

    class Config:
        from_attributes = True


class RestaurantDetail(BaseModel):
    id: int
    name: str
    slug: Optional[str] = None
    cuisine_type: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    image_url: Optional[str] = None
    yelp_url: Optional[str] = None
    description: Optional[str] = None
    price_range: Optional[str] = None
    avg_rating: float = 0.0
    review_count: int = 0
    transactions: Optional[str] = None
    amenities: Optional[list[str]] = None
    keywords: Optional[list[str]] = None
    source: str = "local"
    hours: List[HoursRead] = []
    photos: List[PhotoRead] = []

    class Config:
        from_attributes = True


class RestaurantSearchResponse(BaseModel):
    items: List[RestaurantListItem]
    total: int
    page: int
    page_size: int
    pages: int


class RestaurantUpdate(BaseModel):
    name: Optional[str] = None
    cuisine_type: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    price_range: Optional[str] = None
    amenities: Optional[list[str]] = None
    keywords: Optional[list[str]] = None
    image_url: Optional[str] = None


class RestaurantPlaceItem(BaseModel):
    label: str
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None


class RestaurantImportRequest(BaseModel):
    location: str
    term: str = "restaurants"
    limit: int = 20


class RestaurantImportResponse(BaseModel):
    imported: int
    updated: int
    reviews_imported: int
    places_found: int
    message: str
