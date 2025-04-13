from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict
from app.core.security import get_current_active_user, get_current_admin_user
from app.db.session import get_db
from app.models.models import User, PredictionMarket, MarketStatus, UserRole, Prediction
from app.schemas.market import MarketCreate, MarketUpdate, MarketInDB, MarketWithStats
from app.core.settlement import process_market_settlement
from app.core.pi_payments import process_market_rewards, process_pending_transactions
from app.core.web3_service import Web3Service
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_DOWN
import os

router = APIRouter()
web3_service = Web3Service()

def calculate_market_odds(market: PredictionMarket) -> dict:
    """
    Calculate current odds for a market based on the prediction pools.
    """
    total_pool = market.yes_pool + market.no_pool

    if total_pool == 0:
        return {
            "current_odds": {
                "YES": 2.0,  # Even odds (1/0.5)
                "NO": 2.0
            },
            "implied_probabilities": {
                "YES": 50.0,
                "NO": 50.0
            }
        }

    # Calculate implied probabilities
    yes_prob = market.yes_pool / total_pool
    no_prob = market.no_pool / total_pool

    # Convert to decimal odds (1/probability)
    yes_odds = (1 / yes_prob) if yes_prob > 0 else 0
    no_odds = (1 / no_prob) if no_prob > 0 else 0

    return {
        "current_odds": {
            "YES": round(yes_odds, 2),
            "NO": round(no_odds, 2)
        },
        "implied_probabilities": {
            "YES": round(yes_prob * 100, 2),
            "NO": round(no_prob * 100, 2)
        }
    }

@router.post("/", response_model=MarketInDB)
async def create_market(
    market: MarketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new prediction market (requires admin approval).
    """
    # Validate market timing
    if datetime.utcnow() >= market.end_time:
        raise HTTPException(
            status_code=400,
            detail="Market end time must be in the future"
        )
    
    if market.resolution_time <= market.end_time:
        raise HTTPException(
            status_code=400,
            detail="Resolution time must be after market end time"
        )
    
    # Validate minimum time between end and resolution
    min_resolution_delay = timedelta(hours=1)
    if market.resolution_time - market.end_time < min_resolution_delay:
        raise HTTPException(
            status_code=400,
            detail=f"Resolution time must be at least {min_resolution_delay} after end time"
        )
    
    # Check if user has too many pending markets
    pending_markets_count = db.query(PredictionMarket)\
        .filter(
            PredictionMarket.creator_id == current_user.id,
            PredictionMarket.status == MarketStatus.PENDING
        ).count()
    
    max_pending_markets = 5
    if pending_markets_count >= max_pending_markets:
        raise HTTPException(
            status_code=400,
            detail=f"You cannot have more than {max_pending_markets} pending markets"
        )
    
    try:
        # Create market on blockchain
        blockchain_result = web3_service.create_market(
            title=market.title,
            description=market.description,
            end_time=market.end_time,
            resolution_time=market.resolution_time,
            creator_fee_percentage=int(market.creator_fee_percentage),
            platform_fee_percentage=int(market.platform_fee_percentage),
            private_key=os.getenv("ADMIN_PRIVATE_KEY")  # Admin key for market creation
        )
        
        # Create market in database
        db_market = PredictionMarket(
            **market.model_dump(),
            creator_id=current_user.id,
            status=MarketStatus.PENDING,
            metadata={
                "creation_timestamp": datetime.utcnow().isoformat(),
                "creator_role": current_user.role,
                "initial_validation": {
                    "end_time_valid": True,
                    "resolution_time_valid": True
                },
                "blockchain": {
                    "market_id": blockchain_result["market_id"],
                    "transaction_hash": blockchain_result["transaction_hash"],
                    "block_number": blockchain_result["block_number"]
                }
            }
        )
        
        # Auto-approve if creator is admin
        if current_user.role == UserRole.ADMIN:
            db_market.status = MarketStatus.ACTIVE
            db_market.metadata["auto_approved"] = True
            db_market.metadata["approved_at"] = datetime.utcnow().isoformat()
            db_market.metadata["approved_by"] = current_user.id
            db_market.metadata["approval_type"] = "auto_admin"
        
        db.add(db_market)
        db.commit()
        db.refresh(db_market)
        return db_market
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create market: {str(e)}"
        )

@router.get("/", response_model=List[MarketWithStats])
async def list_markets(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: MarketStatus | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List prediction markets with optional filtering.
    """
    query = db.query(PredictionMarket)
    if status:
        query = query.filter(PredictionMarket.status == status)
    
    markets = query.offset(skip).limit(limit).all()
    
    # Add statistics for each market
    result = []
    for market in markets:
        # Calculate basic stats
        stats = {
            "total_predictions": len(market.predictions),
            "user_prediction_amount": None,
            "user_predicted_outcome": None
        }
        
        # Get user's prediction if exists
        user_prediction = next(
            (p for p in market.predictions if p.user_id == current_user.id),
            None
        )
        if user_prediction:
            stats["user_prediction_amount"] = user_prediction.amount
            stats["user_predicted_outcome"] = user_prediction.predicted_outcome
        
        # Calculate current odds
        odds_data = calculate_market_odds(market)
        stats.update(odds_data)
        
        market_dict = MarketInDB.model_validate(market).model_dump()
        market_dict.update(stats)
        result.append(MarketWithStats(**market_dict))
    
    return result

@router.get("/{market_id}", response_model=MarketWithStats)
async def get_market(
    market_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get detailed information about a specific market.
    """
    market = db.query(PredictionMarket).filter(PredictionMarket.id == market_id).first()
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")
    
    # Get statistics
    stats = {
        "total_predictions": len(market.predictions),
        "user_prediction_amount": None,
        "user_predicted_outcome": None
    }
    
    # Get user's prediction if exists
    user_prediction = next(
        (p for p in market.predictions if p.user_id == current_user.id),
        None
    )
    if user_prediction:
        stats["user_prediction_amount"] = user_prediction.amount
        stats["user_predicted_outcome"] = user_prediction.predicted_outcome
    
    market_dict = MarketInDB.model_validate(market).model_dump()
    market_dict.update(stats)
    return MarketWithStats(**market_dict)

@router.put("/{market_id}", response_model=MarketInDB)
async def update_market(
    market_id: int,
    market_update: MarketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Update market details (admin only).
    """
    db_market = db.query(PredictionMarket).filter(PredictionMarket.id == market_id).first()
    if not db_market:
        raise HTTPException(status_code=404, detail="Market not found")
    
    # Update market fields
    for field, value in market_update.model_dump(exclude_unset=True).items():
        setattr(db_market, field, value)
    
    db.commit()
    db.refresh(db_market)
    return db_market

@router.post("/{market_id}/predict", response_model=Dict)
async def place_prediction(
    market_id: int,
    predicted_outcome: bool,
    amount: Decimal,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Place a prediction on a market.
    """
    db_market = db.query(PredictionMarket).filter(PredictionMarket.id == market_id).first()
    if not db_market:
        raise HTTPException(status_code=404, detail="Market not found")
    
    if db_market.status != MarketStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Market is not active")
    
    if datetime.utcnow() >= db_market.end_time:
        raise HTTPException(status_code=400, detail="Market is closed")
    
    try:
        # Place prediction on blockchain
        blockchain_result = web3_service.place_prediction(
            market_id=db_market.metadata["blockchain"]["market_id"],
            predicted_outcome=predicted_outcome,
            amount=amount,
            private_key=current_user.private_key  # User's private key for prediction
        )
        
        # Create prediction in database
        db_prediction = Prediction(
            user_id=current_user.id,
            market_id=market_id,
            amount=float(amount),
            predicted_outcome="YES" if predicted_outcome else "NO",
            status="active",
            metadata={
                "blockchain": {
                    "transaction_hash": blockchain_result["transaction_hash"],
                    "block_number": blockchain_result["block_number"]
                }
            }
        )
        
        # Update market pools
        if predicted_outcome:
            db_market.yes_pool += float(amount)
        else:
            db_market.no_pool += float(amount)
        db_market.total_pool += float(amount)
        
        db.add(db_prediction)
        db.commit()
        
        return {
            "prediction_id": db_prediction.id,
            "transaction_hash": blockchain_result["transaction_hash"],
            "block_number": blockchain_result["block_number"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to place prediction: {str(e)}"
        )

@router.post("/{market_id}/resolve", response_model=MarketInDB)
async def resolve_market(
    market_id: int,
    correct_outcome: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Resolve a market by setting the correct outcome and processing settlements (admin only).
    """
    if correct_outcome not in ["YES", "NO"]:
        raise HTTPException(
            status_code=400,
            detail='Outcome must be either "YES" or "NO"'
        )
    
    db_market = db.query(PredictionMarket).filter(PredictionMarket.id == market_id).first()
    if not db_market:
        raise HTTPException(status_code=404, detail="Market not found")
    
    if db_market.status != MarketStatus.CLOSED:
        raise HTTPException(status_code=400, detail="Market must be closed before resolution")
    
    try:
        # Resolve market on blockchain
        blockchain_result = web3_service.resolve_market(
            market_id=db_market.metadata["blockchain"]["market_id"],
            outcome=correct_outcome == "YES",
            private_key=os.getenv("ADMIN_PRIVATE_KEY")  # Admin key for resolution
        )
        
        # Update market status and correct outcome
        db_market.status = MarketStatus.SETTLED
        db_market.correct_outcome = correct_outcome
        
        # Process rewards and create transactions
        transactions = process_market_rewards(db_market, db)
        
        # Add transaction processing to background tasks
        background_tasks.add_task(process_pending_transactions, db)
        
        # Update market metadata with settlement information
        db_market.metadata = {
            **db_market.metadata,
            "settlement": {
                "resolved_at": datetime.utcnow().isoformat(),
                "resolved_by": current_user.id,
                "correct_outcome": correct_outcome,
                "total_transactions": len(transactions),
                "total_winners": len([t for t in transactions if t.type == "winnings"]),
                "total_distributed": sum(t.amount for t in transactions if t.type == "winnings"),
                "blockchain": {
                    "transaction_hash": blockchain_result["transaction_hash"],
                    "block_number": blockchain_result["block_number"]
                }
            }
        }
        
        db.commit()
        return db_market
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process market resolution: {str(e)}"
        )

@router.post("/{market_id}/claim", response_model=Dict)
async def claim_rewards(
    market_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Claim rewards for a resolved market.
    """
    db_market = db.query(PredictionMarket).filter(PredictionMarket.id == market_id).first()
    if not db_market:
        raise HTTPException(status_code=404, detail="Market not found")
    
    if db_market.status != MarketStatus.SETTLED:
        raise HTTPException(status_code=400, detail="Market is not settled")
    
    try:
        # Claim rewards on blockchain
        blockchain_result = web3_service.claim_reward(
            market_id=db_market.metadata["blockchain"]["market_id"],
            private_key=current_user.private_key  # User's private key for claiming
        )
        
        return {
            "transaction_hash": blockchain_result["transaction_hash"],
            "block_number": blockchain_result["block_number"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to claim rewards: {str(e)}"
        )

@router.get("/{market_id}/transactions", response_model=List[Dict])
async def get_market_transactions(
    market_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get all transactions related to a specific market (admin only).
    """
    transactions = db.query(Transaction).filter(
        Transaction.metadata.contains({"market_id": market_id})
    ).all()
    
    return [
        {
            "id": tx.id,
            "user_id": tx.user_id,
            "type": tx.type,
            "amount": tx.amount,
            "status": tx.status,
            "reference_id": tx.reference_id,
            "metadata": tx.metadata
        }
        for tx in transactions
    ] 