from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(200), nullable=False)
    cuisine_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    address = Column(String(300), nullable=False)
    city = Column(String(100), nullable=False)
    zip_code = Column(String(20), nullable=True)
    contact_info = Column(String(100), nullable=True)
    hours = Column(JSON, nullable=True)
    pricing_tier = Column(String(10), nullable=True)
    amenities = Column(JSON, nullable=True)
    photos = Column(JSON, nullable=True)
    is_claimed = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    owner = relationship("User", foreign_keys=[owner_id])
    creator = relationship("User", foreign_keys=[created_by])
    reviews = relationship("Review", back_populates="restaurant", cascade="all, delete-orphan")
    favorited_by = relationship("Favorite", back_populates="restaurant", cascade="all, delete-orphan")
