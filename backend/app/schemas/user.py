from __future__ import annotations
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime
from app.models.enums import GenderEnum


class UserRead(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: Optional[str] = None
    about_me: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    languages: Optional[List[str]] = None
    gender: Optional[GenderEnum] = None
    profile_picture_path: Optional[str] = None
    is_owner: bool = False
    account_type: str = "user"
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    about_me: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    languages: Optional[List[str]] = None
    gender: Optional[GenderEnum] = None

    @field_validator("state")
    @classmethod
    def state_max_length(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v) > 10:
            raise ValueError("State must be abbreviated (max 10 chars)")
        return v


class UserWithToken(BaseModel):
    user: UserRead
    access_token: str
    token_type: str = "bearer"
