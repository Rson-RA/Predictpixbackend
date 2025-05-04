from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.schemas.user import UserResponse
from app.schemas.transaction import TransactionBase

class ReferralTransactionBase(BaseModel):
    amount: float
    created_at: datetime

class ReferralTransactionCreate(ReferralTransactionBase):
    user_id: int
    referred_user_id: int

class ReferralTransactionResponse(ReferralTransactionBase):
    id: int
    user_id: int
    referred_user_id: int
    transaction_id: Optional[int] = None
    referred_user: UserResponse
    transaction: Optional[TransactionBase] = None

    class Config:
        from_attributes = True

class ReferralStats(BaseModel):
    total_referrals: int
    total_earnings: float
    recent_referrals: List[ReferralTransactionResponse]

class ReferralResponse(BaseModel):
    referral_code: str
    referral_url: str
    referral_earnings: float
    total_referrals: int
    referred_by: Optional[UserResponse] = None

class ReferralHistoryResponse(BaseModel):
    id: int
    user_id: int
    referred_user_id: int
    amount: float
    created_at: datetime
    transaction_id: Optional[int] = None
    referred_user: UserResponse
    transaction: Optional[TransactionBase] = None

    class Config:
        from_attributes = True

