from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean,
    DateTime, Time, ForeignKey, JSON, func, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.database import Base


class Restaurant(Base):
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True, index=True)
    yelp_id = Column(String(255), nullable=True, unique=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    slug = Column("alias", String(255), nullable=True, index=True)
    cuisine_type = Column("category", String(255), nullable=True, index=True)
    description = Column(Text, nullable=True)
    address = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True, index=True)
    state = Column(String(50), nullable=True)
    zip_code = Column(String(20), nullable=True, index=True)
    country = Column(String(10), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    phone = Column(String(30), nullable=True)
    website = Column(String(500), nullable=True)
    image_url = Column(String(500), nullable=True)
    yelp_url = Column(String(500), nullable=True)
    price_range = Column(String(10), nullable=True)
    avg_rating = Column("rating", Float, default=0.0)
    review_count = Column(Integer, default=0)
    is_closed = Column(Boolean, default=False)
    transactions = Column(String(255), nullable=True)
    hours_raw = Column("hours", JSON, nullable=True)
    amenities = Column(JSON, nullable=True)
    keywords = Column(JSON, nullable=True)
    source = Column(String(30), nullable=False, default="local")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    reviews = relationship(
        "Review",
        back_populates="restaurant",
        cascade="all, delete-orphan",
        primaryjoin="Restaurant.id==Review.business_id",
    )
    hours = relationship(
        "RestaurantHours",
        back_populates="restaurant",
        cascade="all, delete-orphan",
    )
    photos = relationship(
        "RestaurantPhoto",
        back_populates="restaurant",
        cascade="all, delete-orphan",
    )
    ownerships = relationship(
        "RestaurantOwnership",
        back_populates="restaurant",
        cascade="all, delete-orphan",
    )
    views = relationship(
        "RestaurantView",
        back_populates="restaurant",
        cascade="all, delete-orphan",
    )

    @property
    def is_active(self) -> bool:
        return not bool(self.is_closed)

    @property
    def primary_photo(self):
        primary = next((p for p in self.photos if p.is_primary), None)
        return primary.file_path if primary else (self.photos[0].file_path if self.photos else self.image_url)


class RestaurantHours(Base):
    __tablename__ = "restaurant_hours"

    id = Column(Integer, primary_key=True)
    restaurant_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    day_of_week = Column(String(20), nullable=True)
    open_time = Column(Time, nullable=True)
    close_time = Column(Time, nullable=True)
    is_closed = Column(Boolean, default=False)

    restaurant = relationship("Restaurant", back_populates="hours")


class RestaurantPhoto(Base):
    __tablename__ = "restaurant_photos"

    id = Column(Integer, primary_key=True)
    restaurant_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    file_path = Column(String(500), nullable=False)
    caption = Column(String(255), nullable=True)
    is_primary = Column(Boolean, default=False)
    uploaded_at = Column(DateTime, server_default=func.now())

    restaurant = relationship("Restaurant", back_populates="photos")


class RestaurantOwnership(Base):
    __tablename__ = "restaurant_ownerships"
    __table_args__ = (
        UniqueConstraint("restaurant_id", "owner_id", name="uq_restaurant_owner"),
    )

    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(String(30), nullable=False, default="claimed")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    restaurant = relationship("Restaurant", back_populates="ownerships")
    owner = relationship("User", back_populates="restaurant_claims")


class RestaurantView(Base):
    __tablename__ = "restaurant_views"

    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    viewer_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    viewed_at = Column(DateTime, server_default=func.now(), index=True)

    restaurant = relationship("Restaurant", back_populates="views")
    viewer = relationship("User", back_populates="restaurant_views")
