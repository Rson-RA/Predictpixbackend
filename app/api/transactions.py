from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from app.core.security import get_current_active_user
from app.core.pi_auth import pi_auth
from app.db.session import get_db
from app.models.models import User, Transaction, TransactionType
from app.schemas.transaction import TransactionCreate, TransactionInDB, TransactionWithUser

router = APIRouter()

@router.post("/deposit", response_model=TransactionInDB)
async def create_deposit(
    amount: float,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a deposit request using Pi Network.
    """
    try:
        # Create Pi payment request
        payment = await pi_auth.create_payment(
            amount=amount,
            memo=f"Deposit to PredictPix - User: {current_user.username}",
            user_uid=current_user.pi_user_id
        )
        
        # Create transaction record
        transaction = Transaction(
            user_id=current_user.id,
            type=TransactionType.DEPOSIT,
            amount=amount,
            status="pending",
            reference_id=payment["identifier"],
            metadata={"payment_id": payment["identifier"]}
        )
        
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        
        return transaction
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to create deposit: {str(e)}"
        )

@router.post("/withdraw", response_model=TransactionInDB)
async def create_withdrawal(
    amount: float,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a withdrawal request using Pi Network.
    """
    # Check user balance
    if current_user.balance < amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    try:
        # Create Pi payment request
        payment = await pi_auth.create_payment(
            amount=amount,
            memo=f"Withdrawal from PredictPix - User: {current_user.username}",
            user_uid=current_user.pi_user_id
        )
        
        # Create transaction record
        transaction = Transaction(
            user_id=current_user.id,
            type=TransactionType.WITHDRAWAL,
            amount=amount,
            status="pending",
            reference_id=payment["identifier"],
            metadata={"payment_id": payment["identifier"]}
        )
        
        # Update user balance
        current_user.balance -= amount
        
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        
        return transaction
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to create withdrawal: {str(e)}"
        )

@router.get("/", response_model=List[TransactionInDB])
async def list_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    transaction_type: TransactionType | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List user's transactions with optional filtering.
    """
    query = db.query(Transaction).filter(Transaction.user_id == current_user.id)
    
    if transaction_type:
        query = query.filter(Transaction.type == transaction_type)
    
    transactions = query.order_by(Transaction.created_at.desc()).offset(skip).limit(limit).all()
    return transactions

@router.get("/{transaction_id}", response_model=TransactionInDB)
async def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get detailed information about a specific transaction.
    """
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return transaction

@router.post("/verify/{transaction_id}", response_model=TransactionInDB)
async def verify_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Verify a pending transaction with Pi Network.
    """
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    if transaction.status != "pending":
        raise HTTPException(status_code=400, detail="Transaction is not pending")
    
    try:
        # Verify payment with Pi Network
        payment_info = await pi_auth.verify_payment(transaction.metadata["payment_id"])
        
        if payment_info["status"] == "completed":
            transaction.status = "completed"
            transaction.tx_hash = payment_info.get("transaction_hash")
            
            # Update user balance for deposits
            if transaction.type == TransactionType.DEPOSIT:
                current_user.balance += transaction.amount
            
            db.commit()
            db.refresh(transaction)
        else:
            transaction.status = "failed"
            db.commit()
            db.refresh(transaction)
            raise HTTPException(status_code=400, detail="Payment verification failed")
        
        return transaction
    except Exception as e:
        transaction.status = "failed"
        db.commit()
        raise HTTPException(
            status_code=400,
            detail=f"Transaction verification failed: {str(e)}"
        ) 