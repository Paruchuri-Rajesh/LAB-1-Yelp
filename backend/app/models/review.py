from sqlalchemy import (
    Column, Integer, String, Text, SmallInteger,
    Date, DateTime, ForeignKey, UniqueConstraint, func,
)
from sqlalchemy.orm import relationship
from app.database import Base


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint("business_id", "user_id", name="uq_one_review_per_user"),
        UniqueConstraint("external_review_id", name="uq_external_review_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    external_review_id = Column(String(255), nullable=True)
    source = Column(String(30), nullable=False, default="local")
    rating = Column(SmallInteger, nullable=True)
    title = Column(String(200), nullable=True)
    body = Column("review_text", Text, nullable=True)
    author_name = Column("author", String(255), nullable=True)
    author_image_url = Column(String(500), nullable=True)
    source_url = Column(String(500), nullable=True)
    visited_at = Column("review_date", Date, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    restaurant = relationship("Restaurant", back_populates="reviews", primaryjoin="Review.business_id==Restaurant.id")
    user = relationship("User", back_populates="reviews")

    @property
    def restaurant_id(self) -> int:
        return self.business_id


class ReviewPhoto(Base):
    __tablename__ = "review_photos"

    id = Column(Integer, primary_key=True)
    review_id = Column(Integer, ForeignKey("reviews.id"), nullable=False)
    file_path = Column(String(500), nullable=False)
    caption = Column(String(255), nullable=True)
    uploaded_at = Column(DateTime, server_default=func.now())

    review = relationship("Review", back_populates="photos")

# add photos relationship to Review dynamically
Review.photos = relationship("ReviewPhoto", back_populates="review", cascade="all, delete-orphan")
