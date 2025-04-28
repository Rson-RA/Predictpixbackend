from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List
from app.core.security import get_current_active_user, get_current_admin_user
from app.db.session import get_db
from app.models.models import User, Prediction, PredictionMarket, MarketStatus, PredictionStatus
from app.schemas.prediction import PredictionCreate, PredictionInDB, PredictionWithMarket, PredictionFilter
from app.core.config import settings
from datetime import datetime

router = APIRouter()

@router.post("/create", response_model=PredictionInDB)
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
    # if prediction.predicted_outcome not in market.outcome_options:
    #     raise HTTPException(status_code=400, detail="Invalid outcome option")
    
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
    market.yes_pool += prediction.amount if prediction.predicted_outcome == 'yes' else 0
    market.no_pool += prediction.amount if prediction.predicted_outcome == 'no' else 0

    # TODO: create transaction for prediction
    
    db.add(db_prediction)
    db.commit()
    db.refresh(db_prediction)
    
    return db_prediction

@router.get("/", response_model=List[PredictionWithMarket])
async def list_predictions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    filters: PredictionFilter = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List predictions with optional filtering.
    """
    query = db.query(Prediction)\
        .options(joinedload(Prediction.market))\
        .options(joinedload(Prediction.user))\
        .order_by(Prediction.created_at.desc())

    # Apply filters
    if filters.user_id:
        query = query.filter(Prediction.user_id == filters.user_id)
    if filters.market_id:
        query = query.filter(Prediction.market_id == filters.market_id)
    if filters.status:
        query = query.filter(Prediction.status == filters.status)
    if filters.predicted_outcome:
        query = query.filter(Prediction.predicted_outcome == filters.predicted_outcome)

    # Get total count
    total_count = query.count()

    # Apply pagination
    predictions = query.offset(skip).limit(limit).all()

    # Convert to response format
    result = []
    for prediction in predictions:
        prediction_dict = {
            "id": prediction.id,
            "user_id": prediction.user_id,
            "market_id": prediction.market_id,
            "amount": prediction.amount,
            "predicted_outcome": prediction.predicted_outcome,
            "status": prediction.status,
            # "metadata": prediction.metadata,
            "created_at": prediction.created_at,
            "updated_at": prediction.updated_at,
            "market": prediction.market,
            "creator": prediction.user
        }
        result.append(prediction_dict)

    return result

@router.get("/my", response_model=List[PredictionWithMarket])
async def list_my_predictions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List predictions for the current user with optional status filtering.
    """
    query = db.query(Prediction)\
        .options(joinedload(Prediction.market))\
        .filter(Prediction.user_id == current_user.id)\
        .order_by(Prediction.created_at.desc())

    if status:
        query = query.filter(Prediction.status == status)

    predictions = query.offset(skip).limit(limit).all()
    
    result = []
    for prediction in predictions:
        prediction_dict = {
            "id": prediction.id,
            "user_id": prediction.user_id,
            "market_id": prediction.market_id,
            "amount": prediction.amount,
            "predicted_outcome": prediction.predicted_outcome,
            "status": prediction.status,
            # "metadata": prediction.metadata,
            "created_at": prediction.created_at,
            "updated_at": prediction.updated_at,
            "market": prediction.market
        }
        result.append(prediction_dict)

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

@router.put("/{prediction_id}/status", response_model=PredictionWithMarket)
async def update_prediction_status(
    prediction_id: int,
    status: PredictionStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Update prediction status (admin only).
    """
    prediction = db.query(Prediction).filter(Prediction.id == prediction_id).first()
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")

    # Update prediction status
    prediction.status = status
    prediction.updated_at = datetime.utcnow()

    # If prediction is cancelled, refund the user
    if status == PredictionStatus.CANCELLED:
        prediction.user.balance += prediction.amount
        
        # Update market pools
        market = prediction.market
        market.total_pool -= prediction.amount
        if prediction.predicted_outcome == "YES":
            market.yes_pool -= prediction.amount
        else:
            market.no_pool -= prediction.amount

    db.commit()
    db.refresh(prediction)

    # Return prediction with market info
    return {
        "id": prediction.id,
        "user_id": prediction.user_id,
        "market_id": prediction.market_id,
        "amount": prediction.amount,
        "predicted_outcome": prediction.predicted_outcome,
        "status": prediction.status,
        "created_at": prediction.created_at,
        "updated_at": prediction.updated_at,
        "market": prediction.market
    } 