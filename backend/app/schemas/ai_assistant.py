from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ClientLocation(BaseModel):
    latitude: float
    longitude: float


class AIChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[Any]] = None
    client_location: Optional[ClientLocation] = None


class Recommendation(BaseModel):
    id: int
    name: str
    avg_rating: Optional[float] = None
    review_count: Optional[int] = None
    price_range: Optional[str] = None
    cuisine_type: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    image_url: Optional[str] = None
    primary_photo: Optional[str] = None
    source: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    reason: Optional[str] = None


class AIChatResponse(BaseModel):
    assistant_text: str
    recommendations: List[Recommendation]
    conversation_history: Optional[List[Any]] = None
    route: Optional[Dict[str, Any]] = None
    used_current_context: Optional[bool] = None
