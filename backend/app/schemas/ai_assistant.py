from pydantic import BaseModel
from typing import Any, List, Optional


class AIChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[Any]] = None


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
    reason: Optional[str] = None


class AIChatResponse(BaseModel):
    assistant_text: str
    recommendations: List[Recommendation]
    conversation_history: Optional[List[Any]] = None
