from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from app.core.deps import get_db, get_current_admin_user
from app.models.models import User, PredictionMarket, MarketStatus, UserRole, Prediction, Transaction
from app.schemas.admin import UserUpdate, MarketApproval
from app.schemas.market import MarketResponse
from app.schemas.user import UserResponse
from datetime import datetime, timedelta

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/users", response_model=List[UserResponse])
def get_users(
    skip: int = 0,
    limit: int = 100,
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Get all users with filtering options (admin only)"""
    query = db.query(User)
    
    if role:
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    if search:
        query = query.filter(User.username.ilike(f"%{search}%"))
    
    users = query.offset(skip).limit(limit).all()
    return users

@router.get("/users/stats")
def get_user_stats(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Get user statistics (admin only)"""
    total_users = db.query(func.count(User.id)).scalar()
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar()
    admin_users = db.query(func.count(User.id)).filter(User.role == UserRole.ADMIN).scalar()
    
    # Get users with highest balance
    top_users = db.query(User).order_by(desc(User.balance)).limit(5).all()
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "admin_users": admin_users,
        "top_users": [{"username": user.username, "balance": user.balance} for user in top_users]
    }

@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Update user details (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent removing the last admin
    if user.role == UserRole.ADMIN and user_update.role == UserRole.USER:
        admin_count = db.query(func.count(User.id)).filter(User.role == UserRole.ADMIN).scalar()
        if admin_count <= 1:
            raise HTTPException(
                status_code=400,
                detail="Cannot remove the last admin user"
            )
    
    for field, value in user_update.dict(exclude_unset=True).items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    return user

@router.get("/markets/pending", response_model=List[MarketResponse])
def get_pending_markets(
    skip: int = 0,
    limit: int = 100,
    creator_id: Optional[int] = None,
    min_pool: Optional[float] = None,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Get all pending markets with filtering options (admin only)"""
    query = db.query(PredictionMarket).filter(PredictionMarket.status == MarketStatus.PENDING)
    
    if creator_id:
        query = query.filter(PredictionMarket.creator_id == creator_id)
    if min_pool is not None:
        query = query.filter(PredictionMarket.total_pool >= min_pool)
    
    markets = query.offset(skip).limit(limit).all()
    return markets

@router.get("/markets/stats")
def get_market_stats(
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Get market statistics (admin only)"""
    now = datetime.utcnow()
    start_date = now - timedelta(days=days)
    
    total_markets = db.query(func.count(PredictionMarket.id)).scalar()
    active_markets = db.query(func.count(PredictionMarket.id))\
        .filter(PredictionMarket.status == MarketStatus.ACTIVE).scalar()
    pending_markets = db.query(func.count(PredictionMarket.id))\
        .filter(PredictionMarket.status == MarketStatus.PENDING).scalar()
    
    recent_markets = db.query(func.count(PredictionMarket.id))\
        .filter(PredictionMarket.end_time >= start_date).scalar()
    
    total_pool = db.query(func.sum(PredictionMarket.total_pool))\
        .filter(PredictionMarket.status == MarketStatus.ACTIVE).scalar() or 0
    
    return {
        "total_markets": total_markets,
        "active_markets": active_markets,
        "pending_markets": pending_markets,
        "recent_markets": recent_markets,
        "total_active_pool": total_pool
    }

@router.put("/markets/{market_id}/approve", response_model=MarketResponse)
def approve_market(
    market_id: int,
    approval: MarketApproval,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Approve or reject a market (admin only)"""
    market = db.query(PredictionMarket).filter(PredictionMarket.id == market_id).first()
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")
    
    if market.status != MarketStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot modify market in {market.status} status"
        )
    
    if approval.approved:
        market.status = MarketStatus.ACTIVE
    else:
        market.status = MarketStatus.CANCELLED
        # Refund any existing predictions if market is cancelled
        predictions = db.query(Prediction).filter(Prediction.market_id == market_id).all()
        for prediction in predictions:
            prediction.user.balance += prediction.amount
            prediction.status = PredictionStatus.CANCELLED
    
    market.market_metadata = {
        **(market.market_metadata or {}),
        "admin_note": approval.note,
        "approved_by": current_admin.id,
        "approved_at": str(datetime.utcnow())
    }
    
    db.commit()
    db.refresh(market)
    return market 