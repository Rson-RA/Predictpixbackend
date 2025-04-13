from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.models import PredictionStatus

class PredictionBase(BaseModel):
    market_id: int
    amount: float = Field(gt=0)
    predicted_outcome: str

class PredictionCreate(PredictionBase):
    pass

class PredictionUpdate(BaseModel):
    status: PredictionStatus
    potential_winnings: Optional[float] = None

class PredictionInDB(PredictionBase):
    id: int
    user_id: int
    status: PredictionStatus
    potential_winnings: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PredictionWithMarket(PredictionInDB):
    market_title: str
    market_status: str
    market_end_time: datetime 