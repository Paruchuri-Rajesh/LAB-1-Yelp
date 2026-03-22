from pydantic import BaseModel
from typing import Optional, List


class PreferencesUpdate(BaseModel):
    cuisine_preferences: Optional[List[str]] = None
    price_range: Optional[str] = None
    preferred_locations: Optional[List[str]] = None
    dietary_needs: Optional[List[str]] = None
    ambiance_preferences: Optional[List[str]] = None
    sort_preference: Optional[str] = None


class PreferencesOut(BaseModel):
    id: int
    user_id: int
    cuisine_preferences: Optional[List[str]] = None
    price_range: Optional[str] = None
    preferred_locations: Optional[List[str]] = None
    dietary_needs: Optional[List[str]] = None
    ambiance_preferences: Optional[List[str]] = None
    sort_preference: Optional[str] = None

    class Config:
        from_attributes = True
