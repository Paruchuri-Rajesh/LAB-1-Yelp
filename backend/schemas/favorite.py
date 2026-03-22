from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class FavoriteOut(BaseModel):
    id: int
    user_id: int
    restaurant_id: int
    restaurant_name: Optional[str] = None
    restaurant_cuisine: Optional[str] = None
    restaurant_city: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
