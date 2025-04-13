from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.models import UserRole

class UserResponse(BaseModel):
    id: int
    username: str
    pi_user_id: str
    role: UserRole
    balance: float
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 