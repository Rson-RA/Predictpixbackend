from pydantic import BaseModel, Field, validator
from typing import Dict, Optional, Any
from datetime import datetime
from app.models.models import MarketStatus

class Creator(BaseModel):
    id: Optional[int] = None
    username: str

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
    creator: Creator
    status: MarketStatus
    total_pool: float
    yes_pool: float
    no_pool: float
    correct_outcome: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    market_metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
        populate_by_name = True
        alias_generator = lambda x: x.replace('market_metadata', 'metadata')

class MarketWithStats(MarketInDB):
    total_predictions: int
    user_prediction_amount: Optional[float] = None
    user_predicted_outcome: Optional[str] = None
    total_markets_by_creator: Optional[int] = None
    current_odds: Optional[Dict[str, float]] = None  # Current betting odds
    implied_probabilities: Optional[Dict[str, float]] = None  # Probability percentages

class MarketResponse(MarketInDB):
    """Response model for market data in API responses"""
    class Config:
        from_attributes = True
        populate_by_name = True
        alias_generator = lambda x: x.replace('market_metadata', 'metadata')

class MarketReject(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500)

    class Config:
        from_attributes = True 