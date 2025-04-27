from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from app.models.models import PredictionStatus
from app.schemas.market import MarketInDB

class PredictionBase(BaseModel):
    amount: float
    predicted_outcome: str
    # metadata: Optional[Dict[str, Any]] = None

class PredictionCreate(PredictionBase):
    market_id: int

class PredictionUpdate(BaseModel):
    status: PredictionStatus
    potential_winnings: Optional[float] = None

class PredictionInDB(PredictionBase):
    id: int
    user_id: int
    market_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PredictionWithMarket(PredictionInDB):
    market: MarketInDB

    class Config:
        from_attributes = True

class PredictionFilter(BaseModel):
    user_id: Optional[int] = None
    market_id: Optional[int] = None
    status: Optional[str] = None
    predicted_outcome: Optional[str] = None 