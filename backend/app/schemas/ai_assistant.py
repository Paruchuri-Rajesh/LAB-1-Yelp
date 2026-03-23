from pydantic import BaseModel
from typing import Any, List, Optional


class AIChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[Any]] = None


class Recommendation(BaseModel):
    id: int
    name: str
    avg_rating: Optional[float]
    review_count: Optional[int]
    price_range: Optional[str]
    cuisine_type: Optional[str]
    reason: Optional[str]


class AIChatResponse(BaseModel):
    assistant_text: str
    recommendations: List[Recommendation]
    conversation_history: Optional[List[Any]] = None
