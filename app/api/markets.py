from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Dict
from app.core.security import get_current_active_user, get_current_admin_user
from app.db.session import get_db
from app.models.models import User, PredictionMarket, MarketStatus, UserRole, Prediction, Reward, Transaction, TransactionType, TransactionStatus
from app.schemas.market import MarketCreate, MarketUpdate, MarketInDB, MarketWithStats, MarketReject
from app.core.settlement import process_market_settlement
from app.core.pi_payments import process_market_rewards, process_pending_transactions
from app.core.web3_service import Web3Service
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_DOWN
import os
from app.core.socket import SocketManager

router = APIRouter()
web3_service = Web3Service()
socket_manager = SocketManager()

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

def convert_market_to_dict(market: PredictionMarket) -> dict:
    """Helper function to convert market to dictionary with proper metadata handling"""
    creator_info = {
        "creator": {
            "id": market.creator.id,
            "username": market.creator.username
        } if market.creator else {
            "id": None,
            "username": "Unknown"
        }
    }
    
    # Convert SQLAlchemy model to dict, explicitly handling metadata
    metadata = {}
    if market.market_metadata is not None:
        if isinstance(market.market_metadata, dict):
            metadata = market.market_metadata
        else:
            # Handle SQLAlchemy JSON type or other object types
            try:
                metadata = dict(market.market_metadata)
            except (TypeError, ValueError):
                # If conversion fails, try to get the raw value
                metadata = market.market_metadata._asdict() if hasattr(market.market_metadata, '_asdict') else {}
    
    return {
        "id": market.id,
        "title": market.title,
        "description": market.description,
        "creator_id": market.creator_id,
        "end_time": market.end_time,
        "resolution_time": market.resolution_time,
        "status": market.status,
        "total_pool": market.total_pool,
        "yes_pool": market.yes_pool,
        "no_pool": market.no_pool,
        "correct_outcome": market.correct_outcome,
        "created_at": market.created_at,
        "updated_at": market.updated_at,
        "creator_fee_percentage": market.creator_fee_percentage,
        "platform_fee_percentage": market.platform_fee_percentage,
        "market_metadata": metadata,
        **creator_info
    }

@router.post("/create", response_model=MarketInDB)
async def create_market(
    market: MarketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new prediction market (requires admin approval).
    """
    # Get current UTC time as timezone-aware datetime
    now = datetime.now(timezone.utc)
    
    # Validate market timing
    if now >= market.end_time:
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
        # blockchain_result = web3_service.create_market(
        #     title=market.title,
        #     description=market.description,
        #     end_time=market.end_time,
        #     resolution_time=market.resolution_time,
        #     creator_fee_percentage=int(market.creator_fee_percentage),
        #     platform_fee_percentage=int(market.platform_fee_percentage),
        #     private_key=os.getenv("ADMIN_PRIVATE_KEY")  # Admin key for market creation
        # )
        blockchain_result = {
            "market_id": 1,
            "transaction_hash": "0x1234567890abcdef",
            "block_number": 1234567890
        }
        
        # Create market in database
        market_data = market.model_dump()
        market_metadata = {
            "creation_timestamp": now.isoformat(),
            "creator_role": current_user.role,
            "initial_validation": {
                "end_time_valid": True,
                "resolution_time_valid": True
            },
            "blockchain": {
                "market_id": blockchain_result["market_id"],
                "transaction_hash": blockchain_result["transaction_hash"],
                "block_number": blockchain_result["block_number"]
            },
            "market": market.metadata
        }
        
        db_market = PredictionMarket(
            **market_data,
            creator_id=current_user.id,
            status=MarketStatus.PENDING,
            market_metadata=market_metadata
        )
        
        db.add(db_market)
        db.commit()
        db.refresh(db_market)
        
        # Add transaction for market creation
        market_creation_tx = Transaction(
            user_id=current_user.id,
            amount=None,  # No direct amount for market creation
            status=TransactionStatus.PENDING,
            transaction_type=TransactionType.MARKET_CREATION,
            tx_hash=blockchain_result["transaction_hash"],
            reference_id=str(db_market.id),
            transaction_metadata={
                "blockchain": market_metadata["blockchain"],
                "market": market_metadata["market"],
                "creation_timestamp": now.isoformat(),
            }
        )
        db.add(market_creation_tx)
        db.commit()
        db.refresh(market_creation_tx)
        
        # Convert to response format
        response_data = db_market.to_dict()
        return response_data
        
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
    print(f"Listing markets with status: {status}")
    query = db.query(PredictionMarket)\
        .options(joinedload(PredictionMarket.creator))\
        .order_by(PredictionMarket.created_at.desc())
    
    if status:
        query = query.filter(PredictionMarket.status == status)
    
    markets = query.offset(skip).limit(limit).all()
    result = []
    
    for market in markets:
        # Get total predictions for this market
        total_predictions = len(market.predictions)
        
        # Get user's prediction if exists
        user_prediction = next(
            (p for p in market.predictions if p.user_id == current_user.id),
            None
        )
        
        # Get total markets by creator
        total_markets_by_creator = db.query(PredictionMarket)\
            .filter(PredictionMarket.creator_id == market.creator_id)\
            .count()
        
        # Calculate odds
        odds_data = calculate_market_odds(market)
        
        # Convert market to dict and add stats
        market_dict = market.to_dict()
        market_dict.update({
            "total_predictions": total_predictions,
            "user_prediction_amount": user_prediction.amount if user_prediction else None,
            "user_predicted_outcome": user_prediction.predicted_outcome if user_prediction else None,
            "total_markets_by_creator": total_markets_by_creator,
            **odds_data
        })
        result.append(market_dict)
    
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
    market = db.query(PredictionMarket)\
        .options(joinedload(PredictionMarket.creator))\
        .filter(PredictionMarket.id == market_id)\
        .first()
    
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")
    
    # Get total predictions for this market
    total_predictions = len(market.predictions)
    
    # Get user's prediction if exists
    user_prediction = next(
        (p for p in market.predictions if p.user_id == current_user.id),
        None
    )
    
    # Get total markets by creator
    total_markets_by_creator = db.query(PredictionMarket)\
        .filter(PredictionMarket.creator_id == market.creator_id)\
        .count()
    
    # Calculate odds
    odds_data = calculate_market_odds(market)
    
    # Convert market to dict and add stats
    market_dict = market.to_dict()
    market_dict.update({
        "total_predictions": total_predictions,
        "user_prediction_amount": user_prediction.amount if user_prediction else None,
        "user_predicted_outcome": user_prediction.predicted_outcome if user_prediction else None,
        "total_markets_by_creator": total_markets_by_creator,
        **odds_data
    })
    
    return market_dict

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
    update_data = market_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_market, field, value)
    
    # Update metadata with update information
    now = datetime.now(timezone.utc)
    current_metadata = db_market.market_metadata or {}
    db_market.market_metadata = {
        **current_metadata,
        "last_update": {
            "updated_at": now.isoformat(),
            "updated_by": current_user.id,
            "updated_fields": list(update_data.keys())
        }
    }
    
    db.commit()
    db.refresh(db_market)
    socket_manager.broadcast_to_all(f"Market {db_market.id} updated")
    return db_market.to_dict()

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
        # blockchain_result = web3_service.place_prediction(
        #     market_id=db_market.market_metadata["blockchain"]["market_id"],
        #     predicted_outcome=predicted_outcome,
        #     amount=amount,
        #     private_key=current_user.private_key  # User's private key for prediction
        # )
        blockchain_result = {
            "transaction_hash": "0x1234567890abcdef",
            "block_number": 1234567890
        }
        # Create prediction in database
        db_prediction = Prediction(
            user_id=current_user.id,
            market_id=market_id,
            amount=float(amount),
            predicted_outcome="YES" if predicted_outcome else "NO",
            status="pending",
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
            market_id=db_market.market_metadata["blockchain"]["market_id"],
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
        db_market.market_metadata = {
            **db_market.market_metadata,
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
            market_id=db_market.market_metadata["blockchain"]["market_id"],
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

@router.post("/{market_id}/approve", response_model=MarketInDB)
async def approve_market(
    market_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Approve a pending market (admin only).
    """
    db_market = db.query(PredictionMarket).filter(PredictionMarket.id == market_id).first()
    if not db_market:
        raise HTTPException(status_code=404, detail="Market not found")
    
    if db_market.status != MarketStatus.PENDING:
        raise HTTPException(status_code=400, detail="Only pending markets can be approved")
    
    try:
        # Update market status
        db_market.status = MarketStatus.ACTIVE
        
        # Update metadata with approval information
        now = datetime.now(timezone.utc)
        current_metadata = db_market.market_metadata or {}
        db_market.market_metadata = {
            **current_metadata,
            "approval": {
                "approved_at": now.isoformat(),
                "approved_by": current_user.id,
                "approver_role": current_user.role
            }
        }
        
        db.commit()
        db.refresh(db_market)
        return db_market.to_dict()
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to approve market: {str(e)}"
        )

@router.post("/{market_id}/reject", response_model=MarketInDB)
async def reject_market(
    market_id: int,
    reject_data: MarketReject,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Reject a pending market (admin only).
    """
    db_market = db.query(PredictionMarket).filter(PredictionMarket.id == market_id).first()
    if not db_market:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market not found"
        )
    
    if db_market.status != MarketStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending markets can be rejected"
        )
    
    try:
        # Update market status
        db_market.status = MarketStatus.CANCELLED
        
        # Update metadata with rejection information
        now = datetime.now(timezone.utc)
        current_metadata = db_market.market_metadata or {}
        db_market.market_metadata = {
            **current_metadata,
            "rejected_at": now.isoformat(),
            "rejected_by": current_user.id,
            "rejection_reason": reject_data.reason
        }
        
        db.commit()
        db.refresh(db_market)
        return db_market.to_dict()
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reject market: {str(e)}"
        )

@router.delete("/{market_id}", response_model=Dict)
async def delete_market(
    market_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Delete a market and all its related data (admin only).
    """
    db_market = db.query(PredictionMarket).filter(PredictionMarket.id == market_id).first()
    if not db_market:
        raise HTTPException(status_code=404, detail="Market not found")
    
    try:
        # Delete all predictions for this market
        db.query(Prediction).filter(Prediction.market_id == market_id).delete()
        
        # Delete all rewards for this market
        db.query(Reward).filter(Reward.market_id == market_id).delete()
        
        # Delete the market itself
        db.delete(db_market)
        db.commit()
        
        return {
            "status": "success",
            "message": f"Market {market_id} and all related data have been deleted"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete market: {str(e)}"
        ) 