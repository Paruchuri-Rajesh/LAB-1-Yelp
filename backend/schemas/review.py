from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ReviewCreate(BaseModel):
    restaurant_id: int
    rating: int
    comment: str


class ReviewUpdate(BaseModel):
    rating: Optional[int] = None
    comment: Optional[str] = None


class ReviewOut(BaseModel):
    id: int
    user_id: int
    user_name: Optional[str] = None
    restaurant_id: int
    restaurant_name: Optional[str] = None
    rating: int
    comment: str
    photos: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
