from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from app.core.security import get_current_active_user
from app.core.pi_auth import pi_auth
from app.db.session import get_db
from app.models.models import User, Transaction, TransactionType, UserRole
from app.schemas.transaction import (
    TransactionCreate,
    TransactionUpdate,
    TransactionInDB,
    TransactionWithUser,
    TransactionFilter
)
from app.crud import transaction as crud_transaction

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

@router.get("/", response_model=List[TransactionWithUser])
def get_transactions(
    user_id: Optional[int] = None,
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    transaction_type: Optional[TransactionType] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all transactions with optional filtering.
    Only admin users can see all transactions, regular users can only see their own.
    """
    filters = TransactionFilter(
        user_id=user_id,
        status=status,
        start_date=start_date,
        end_date=end_date,
        type=transaction_type
    )
    
    # Regular users can only see their own transactions
    if current_user.role != UserRole.ADMIN:
        filters.user_id = current_user.id
        
    transactions = crud_transaction.get_transactions(db, filters=filters, skip=skip, limit=limit)
    return transactions

@router.get("/{transaction_id}", response_model=TransactionWithUser)
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a specific transaction by ID.
    Only admin users can see all transactions, regular users can only see their own.
    """
    transaction = crud_transaction.get_transaction(db, transaction_id)
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
        
    if current_user.role != UserRole.ADMIN and transaction.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this transaction")
        
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
    transaction = crud_transaction.get_transaction(db, transaction_id)
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    if current_user.role != UserRole.ADMIN and transaction.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to verify this transaction")
    
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

@router.put("/{transaction_id}", response_model=TransactionInDB)
async def update_transaction(
    transaction_id: int,
    transaction_update: TransactionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a transaction (admin only).
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to update transactions")
        
    transaction = crud_transaction.update_transaction(db, transaction_id, transaction_update)
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
        
    return transaction

@router.delete("/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a transaction.
    Only admin users can delete transactions.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to delete transactions")
        
    transaction = crud_transaction.delete_transaction(db, transaction_id)
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
        
    return {"message": "Transaction deleted successfully"} 