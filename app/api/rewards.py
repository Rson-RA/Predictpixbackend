from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.security import get_current_active_user
from app.db.session import get_db
from app.models.models import User, Reward, RewardStatus
from datetime import datetime
from pydantic import BaseModel

router = APIRouter()

class RewardResponse(BaseModel):
    id: int
    user_id: int
    prediction_id: int
    market_id: int
    amount: float
    original_prediction_amount: float
    reward_multiplier: float
    status: RewardStatus
    created_at: datetime
    processed_at: Optional[datetime] = None
    metadata: dict
    market_title: str
    prediction_outcome: str

@router.get("/", response_model=List[RewardResponse])
async def list_rewards(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[RewardStatus] = None,
    market_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List rewards for the current user with optional filtering.
    """
    query = db.query(Reward).filter(Reward.user_id == current_user.id)
    
    if status:
        query = query.filter(Reward.status == status)
    if market_id:
        query = query.filter(Reward.market_id == market_id)
    
    rewards = query.order_by(Reward.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        RewardResponse(
            **{
                **reward.__dict__,
                "market_title": reward.market.title,
                "prediction_outcome": reward.prediction.predicted_outcome
            }
        )
        for reward in rewards
    ]

@router.get("/{reward_id}", response_model=RewardResponse)
async def get_reward(
    reward_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get detailed information about a specific reward.
    """
    reward = db.query(Reward).filter(
        Reward.id == reward_id,
        Reward.user_id == current_user.id
    ).first()
    
    if not reward:
        raise HTTPException(status_code=404, detail="Reward not found")
    
    return RewardResponse(
        **{
            **reward.__dict__,
            "market_title": reward.market.title,
            "prediction_outcome": reward.prediction.predicted_outcome
        }
    )

@router.get("/stats/summary")
async def get_reward_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get summary statistics about user's rewards.
    """
    total_rewards = db.query(Reward).filter(
        Reward.user_id == current_user.id
    ).count()
    
    processed_rewards = db.query(Reward).filter(
        Reward.user_id == current_user.id,
        Reward.status == RewardStatus.PROCESSED
    ).count()
    
    total_amount = db.query(func.sum(Reward.amount)).filter(
        Reward.user_id == current_user.id,
        Reward.status == RewardStatus.PROCESSED
    ).scalar() or 0
    
    best_multiplier = db.query(func.max(Reward.reward_multiplier)).filter(
        Reward.user_id == current_user.id
    ).scalar() or 0
    
    return {
        "total_rewards": total_rewards,
        "processed_rewards": processed_rewards,
        "pending_rewards": total_rewards - processed_rewards,
        "total_amount_earned": float(total_amount),
        "best_reward_multiplier": float(best_multiplier),
        "success_rate": (processed_rewards / total_rewards * 100) if total_rewards > 0 else 0
    } 