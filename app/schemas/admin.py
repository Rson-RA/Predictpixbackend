from pydantic import BaseModel, Field
from typing import Optional, List
from app.models.models import UserRole
from datetime import datetime

class UserUpdate(BaseModel):
    username: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    balance: Optional[float] = Field(None, ge=0)

    class Config:
        from_attributes = True

class UserStats(BaseModel):
    total_users: int
    active_users: int
    admin_users: int
    top_users: List[dict]

    class Config:
        from_attributes = True

class MarketApproval(BaseModel):
    approved: bool
    note: Optional[str] = Field(None, max_length=500)

    class Config:
        from_attributes = True

class MarketStats(BaseModel):
    total_markets: int
    active_markets: int
    pending_markets: int
    recent_markets: int
    total_active_pool: float

    class Config:
        from_attributes = True 