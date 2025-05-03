from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List
from app.core.security import get_current_active_user, get_current_admin_user
from app.db.session import get_db
from app.models.models import User, Prediction, PredictionMarket, MarketStatus, PredictionStatus, Transaction, TransactionType, TransactionStatus
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

    # Create transaction for prediction
    db.add(db_prediction)
    db.flush()  # To get db_prediction.id
    prediction_tx = Transaction(
        user_id=current_user.id,
        amount=prediction.amount,
        status=TransactionStatus.PENDING,
        transaction_type=TransactionType.PREDICTION,
        reference_id=str(db_prediction.id),
        transaction_metadata={
            "market_id": prediction.market_id,
            "predicted_outcome": prediction.predicted_outcome
        }
    )
    db.add(prediction_tx)
    
    db.commit()
    db.refresh(db_prediction)
    # Attach creator field for response validation
    creator_dict = {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "avatar_url": current_user.avatar_url,
        "firstname": current_user.firstname,
        "lastname": current_user.lastname
    }
    user_dict = {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "avatar_url": current_user.avatar_url,
        "firstname": current_user.firstname,
        "lastname": current_user.lastname
    }
    # Serialize market to match MarketInDB schema
    market = db_prediction.market
    if market:
        market_dict = {
            "id": market.id,
            "creator_id": market.creator_id,
            "creator": {"id": market.creator.id if market.creator else None, "username": market.creator.username if market.creator else ""},
            "title": market.title,
            "description": market.description,
            "end_time": market.end_time.isoformat() if market.end_time else None,
            "resolution_time": market.resolution_time.isoformat() if market.resolution_time else None,
            "creator_fee_percentage": market.creator_fee_percentage,
            "platform_fee_percentage": market.platform_fee_percentage,
            "status": market.status,
            "total_pool": market.total_pool,
            "yes_pool": market.yes_pool,
            "no_pool": market.no_pool,
            "correct_outcome": market.correct_outcome,
            "created_at": market.created_at.isoformat() if market.created_at else None,
            "updated_at": market.updated_at.isoformat() if market.updated_at else None,
            "market_metadata": dict(market.market_metadata) if market.market_metadata else None
        }
    else:
        market_dict = None
    response_dict = {
        **db_prediction.__dict__,
        "creator": creator_dict,
        "market": market_dict,
        # Ensure datetimes are serializable
        "created_at": db_prediction.created_at.isoformat() if db_prediction.created_at else None,
        "updated_at": db_prediction.updated_at.isoformat() if db_prediction.updated_at else None
    }
    # Remove SQLAlchemy state if present
    response_dict.pop('_sa_instance_state', None)
    response_dict.pop('user', None)
    return response_dict

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
        user = prediction.user
        user_dict = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "avatar_url": user.avatar_url,
            "firstname": user.firstname,
            "lastname": user.lastname
        } if user else None
        # Serialize market to match MarketInDB schema
        market = prediction.market
        if market:
            market_dict = {
                "id": market.id,
                "creator_id": market.creator_id,
                "creator": {"id": market.creator.id if market.creator else None, "username": market.creator.username if market.creator else ""},
                "title": market.title,
                "description": market.description,
                "end_time": market.end_time.isoformat() if market.end_time else None,
                "resolution_time": market.resolution_time.isoformat() if market.resolution_time else None,
                "creator_fee_percentage": market.creator_fee_percentage,
                "platform_fee_percentage": market.platform_fee_percentage,
                "status": market.status,
                "tier": market.tier,
                "total_pool": market.total_pool,
                "yes_pool": market.yes_pool,
                "no_pool": market.no_pool,
                "correct_outcome": market.correct_outcome,
                "created_at": market.created_at.isoformat() if market.created_at else None,
                "updated_at": market.updated_at.isoformat() if market.updated_at else None,
                "market_metadata": dict(market.market_metadata) if market.market_metadata else None
            }
        else:
            market_dict = None
        prediction_dict = {
            "id": prediction.id,
            "user_id": prediction.user_id,
            "market_id": prediction.market_id,
            "amount": prediction.amount,
            "predicted_outcome": prediction.predicted_outcome,
            "status": prediction.status,
            # "metadata": prediction.metadata,
            "created_at": prediction.created_at.isoformat() if prediction.created_at else None,
            "updated_at": prediction.updated_at.isoformat() if prediction.updated_at else None,
            "market": market_dict,
            "creator": user_dict
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