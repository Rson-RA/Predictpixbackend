from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from app.models.models import UserRole

class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: str
    is_active: bool
    avatar_url: Optional[str] = None
    firstname: Optional[str] = None
    lastname: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    avatar_url: Optional[str] = None
    firstname: Optional[str] = None
    lastname: Optional[str] = None

class UserResponse(UserBase):
    id: int
    balance: float
    referral_code: str
    total_predictions: int = 0
    total_earnings: float = 0.0
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True 

class UserPortfolioResponse(UserBase):
    id: int
    balance: float
    referral_code: str
    earnings_in_24h: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True 