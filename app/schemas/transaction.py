from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime
from app.models.models import TransactionType

class TransactionBase(BaseModel):
    type: TransactionType
    amount: float = Field(gt=0)
    reference_id: Optional[str] = None
    metadata: Optional[Dict] = None

class TransactionCreate(TransactionBase):
    pass

class TransactionUpdate(BaseModel):
    status: str
    tx_hash: Optional[str] = None

class TransactionInDB(TransactionBase):
    id: int
    user_id: int
    status: str
    tx_hash: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TransactionWithUser(TransactionInDB):
    username: str 