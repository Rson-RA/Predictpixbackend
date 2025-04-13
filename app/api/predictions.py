from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from app.core.security import get_current_active_user
from app.db.session import get_db
from app.models.models import User, Prediction, PredictionMarket, MarketStatus, PredictionStatus
from app.schemas.prediction import PredictionCreate, PredictionInDB, PredictionWithMarket
from app.core.config import settings

router = APIRouter()

@router.post("/", response_model=PredictionInDB)
async def create_prediction(
    prediction: PredictionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new prediction (bet) on a market.
    """
    # Validate market exists and is active
    market = db.query(PredictionMarket).filter(PredictionMarket.id == prediction.market_id).first()
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")
    
    if market.status != MarketStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Market is not active")
    
    # Validate prediction amount
    if prediction.amount < settings.MIN_PREDICTION_AMOUNT:
        raise HTTPException(
            status_code=400,
            detail=f"Minimum prediction amount is {settings.MIN_PREDICTION_AMOUNT} PI"
        )
    
    if prediction.amount > settings.MAX_PREDICTION_AMOUNT:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum prediction amount is {settings.MAX_PREDICTION_AMOUNT} PI"
        )
    
    # Validate outcome option
    if prediction.predicted_outcome not in market.outcome_options:
        raise HTTPException(status_code=400, detail="Invalid outcome option")
    
    # Check user balance
    if current_user.balance < prediction.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    # Create prediction
    db_prediction = Prediction(
        **prediction.model_dump(),
        user_id=current_user.id,
        status=PredictionStatus.PENDING
    )
    
    # Update user balance
    current_user.balance -= prediction.amount
    
    # Update market total pool
    market.total_pool += prediction.amount
    
    db.add(db_prediction)
    db.commit()
    db.refresh(db_prediction)
    
    return db_prediction

@router.get("/", response_model=List[PredictionWithMarket])
async def list_predictions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    market_id: int | None = None,
    status: PredictionStatus | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List user's predictions with optional filtering.
    """
    query = db.query(Prediction).filter(Prediction.user_id == current_user.id)
    
    if market_id:
        query = query.filter(Prediction.market_id == market_id)
    
    if status:
        query = query.filter(Prediction.status == status)
    
    predictions = query.offset(skip).limit(limit).all()
    
    # Add market information to predictions
    result = []
    for pred in predictions:
        market = pred.market
        pred_dict = PredictionInDB.model_validate(pred).model_dump()
        pred_dict.update({
            "market_title": market.title,
            "market_status": market.status,
            "market_end_time": market.end_time
        })
        result.append(PredictionWithMarket(**pred_dict))
    
    return result

@router.get("/{prediction_id}", response_model=PredictionWithMarket)
async def get_prediction(
    prediction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get detailed information about a specific prediction.
    """
    prediction = db.query(Prediction).filter(
        Prediction.id == prediction_id,
        Prediction.user_id == current_user.id
    ).first()
    
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    
    market = prediction.market
    pred_dict = PredictionInDB.model_validate(prediction).model_dump()
    pred_dict.update({
        "market_title": market.title,
        "market_status": market.status,
        "market_end_time": market.end_time
    })
    
    return PredictionWithMarket(**pred_dict) 