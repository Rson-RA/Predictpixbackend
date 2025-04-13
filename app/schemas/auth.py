from pydantic import BaseModel, EmailStr
from typing import Optional
from app.models.models import UserRole
from datetime import datetime

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    pi_user_id: str | None = None

class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    username: str
    email: str | None = None
    phone_number: str | None = None
    role: UserRole
    created_at: datetime
    updated_at: datetime

class AdminLoginRequest(BaseModel):
    username: str
    password: str

class EmailLoginRequest(BaseModel):
    email: EmailStr
    password: str

class UpdateUserRequest(BaseModel):
    email: EmailStr | None = None
    phone_number: str | None = None
    password: str | None = None

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "phone_number": "+1234567890",
                "password": "newpassword123"
            }
        } 