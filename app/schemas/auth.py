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
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    id: int
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    role: UserRole
    balance: float
    referral_code: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    avatar_url: Optional[str] = None

class AdminLoginRequest(BaseModel):
    username: str
    password: str

class EmailLoginRequest(BaseModel):
    email: EmailStr
    password: str

class UpdateUserRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    password: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "phone_number": "+1234567890",
                "password": "newpassword123"
            }
        }

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class PiLoginRequest(BaseModel):
    pi_token: str

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    username: Optional[str] = None
    referral_code: Optional[str] = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str 