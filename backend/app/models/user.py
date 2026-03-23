from sqlalchemy import (
    Column, Integer, String, Text, Boolean,
    Enum, DateTime, JSON, ForeignKey, func,
)
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.enums import GenderEnum, PriceRangeEnum, SortPreferenceEnum


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    about_me = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(10), nullable=True)
    country = Column(String(100), nullable=True)
    languages = Column(JSON, nullable=True)
    gender = Column(Enum(GenderEnum), nullable=True)
    profile_picture_path = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    preferences = relationship(
        "UserPreference",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    reviews = relationship("Review", back_populates="user")
    owner_profile = relationship(
        "OwnerProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    restaurant_claims = relationship(
        "RestaurantOwnership",
        back_populates="owner",
        cascade="all, delete-orphan",
    )
    restaurant_views = relationship("RestaurantView", back_populates="viewer")
    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")

    @property
    def is_owner(self) -> bool:
        return self.owner_profile is not None

    @property
    def account_type(self) -> str:
        return "owner" if self.is_owner else "user"


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    cuisine_preferences = Column(JSON, nullable=True)
    price_range = Column(Enum(PriceRangeEnum), nullable=True)
    search_radius_miles = Column(Integer, default=10)
    dietary_restrictions = Column(JSON, nullable=True)
    ambiance_preferences = Column(JSON, nullable=True)
    sort_preference = Column(Enum(SortPreferenceEnum), default=SortPreferenceEnum.rating)
    preferred_locations = Column(JSON, nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="preferences")


class OwnerProfile(Base):
    __tablename__ = "owner_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    business_name = Column(String(255), nullable=True)
    restaurant_location = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="owner_profile")
