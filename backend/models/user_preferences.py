from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database import Base


class UserPreferences(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    cuisine_preferences = Column(JSON, nullable=True)
    price_range = Column(String(10), nullable=True)
    preferred_locations = Column(JSON, nullable=True)
    dietary_needs = Column(JSON, nullable=True)
    ambiance_preferences = Column(JSON, nullable=True)
    sort_preference = Column(String(20), nullable=True, default="rating")

    user = relationship("User", back_populates="preferences")
