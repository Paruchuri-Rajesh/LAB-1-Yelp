from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from app.database import Base


class AIInteraction(Base):
    __tablename__ = "ai_interactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    query = Column(Text, nullable=False)
    conversation_history = Column(JSON, nullable=True)
    assistant_text = Column(Text, nullable=True)
    recommendations = Column(JSON, nullable=True)
    # 'metadata' is a reserved attribute name in SQLAlchemy declarative base.
    # Use 'meta' to store arbitrary JSON metadata.
    meta = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User")
