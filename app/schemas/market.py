from pydantic import BaseModel, Field, validator
from typing import Dict, Optional
from datetime import datetime
from app.models.models import MarketStatus

class MarketBase(BaseModel):
    title: str
    description: str
    end_time: datetime
    resolution_time: datetime
    creator_fee_percentage: float = Field(ge=0, le=5)
    platform_fee_percentage: float = Field(ge=0, le=5)

class MarketCreate(MarketBase):
    pass

class MarketUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    end_time: Optional[datetime] = None
    resolution_time: Optional[datetime] = None
    status: Optional[MarketStatus] = None
    correct_outcome: Optional[str] = None

    @validator("correct_outcome")
    def validate_correct_outcome(cls, v):
        if v and v not in ["YES", "NO"]:
            raise ValueError('Outcome must be either "YES" or "NO"')
        return v

class MarketInDB(MarketBase):
    id: int
    creator_id: int
    status: MarketStatus
    total_pool: float
    yes_pool: float
    no_pool: float
    correct_outcome: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict] = None

    class Config:
        from_attributes = True

class MarketWithStats(MarketInDB):
    total_predictions: int
    user_prediction_amount: Optional[float] = None
    user_predicted_outcome: Optional[str] = None
    creator_username: Optional[str] = None
    total_markets_by_creator: Optional[int] = None
    current_odds: Optional[Dict[str, float]] = None  # Current betting odds
    implied_probabilities: Optional[Dict[str, float]] = None  # Probability percentages

class MarketResponse(MarketInDB):
    """Response model for market data in API responses"""
    class Config:
        from_attributes = True 