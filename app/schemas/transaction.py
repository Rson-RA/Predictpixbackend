from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.models import TransactionStatus, TransactionType

class TransactionBase(BaseModel):
    amount: float
    status: str = TransactionStatus.PENDING
    transaction_type: str

class TransactionCreate(TransactionBase):
    user_id: int

class TransactionUpdate(BaseModel):
    status: Optional[str] = None
    transaction_type: Optional[str] = None
    amount: Optional[float] = None

class TransactionInDB(TransactionBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TransactionWithUser(TransactionInDB):
    user: dict

    class Config:
        from_attributes = True

class TransactionFilter(BaseModel):
    user_id: Optional[int] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None 