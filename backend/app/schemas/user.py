from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None


class UserCreate(UserBase):
    pass


class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    picture: Optional[str] = None
    youtube_linked: bool = False
    has_watch_history: bool = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
