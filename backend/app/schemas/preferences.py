from __future__ import annotations
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.enums import PriceRangeEnum, SortPreferenceEnum


class PreferencesRead(BaseModel):
    id: int
    user_id: int
    cuisine_preferences: Optional[List[str]] = None
    price_range: Optional[PriceRangeEnum] = None
    search_radius_miles: Optional[int] = 10
    dietary_restrictions: Optional[List[str]] = None
    ambiance_preferences: Optional[List[str]] = None
    preferred_locations: Optional[List[str]] = None
    sort_preference: Optional[SortPreferenceEnum] = SortPreferenceEnum.rating
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PreferencesUpdate(BaseModel):
    cuisine_preferences: Optional[List[str]] = None
    price_range: Optional[PriceRangeEnum] = None
    search_radius_miles: Optional[int] = None
    dietary_restrictions: Optional[List[str]] = None
    ambiance_preferences: Optional[List[str]] = None
    preferred_locations: Optional[List[str]] = None
    sort_preference: Optional[SortPreferenceEnum] = None
