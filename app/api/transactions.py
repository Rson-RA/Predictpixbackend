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
    query = db.query(Transaction)
    if user_id:
        query = query.filter(Transaction.user_id == user_id)
    if status:
        query = query.filter(Transaction.status == status)
    if start_date:
        query = query.filter(Transaction.created_at >= start_date)
    if end_date:
        query = query.filter(Transaction.created_at <= end_date)
    if transaction_type:
        query = query.filter(Transaction.transaction_type == transaction_type)
    if current_user.role != UserRole.ADMIN:
        query = query.filter(Transaction.user_id == current_user.id)
    transactions = query.offset(skip).limit(limit).all()
    # Attach user as dict for TransactionWithUser
    result = []
    for tx in transactions:
        tx_dict = tx.__dict__.copy()
        tx_dict.pop('_sa_instance_state', None)
        tx_dict['user'] = {
            'id': tx.user.id,
            'username': tx.user.username,
            'email': tx.user.email,
            'role': tx.user.role,
            'is_active': tx.user.is_active,
            'avatar_url': tx.user.avatar_url,
            'firstname': tx.user.firstname,
            'lastname': tx.user.lastname
        } if tx.user else None
        result.append(tx_dict)
    return result

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
    tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if tx is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if current_user.role != UserRole.ADMIN and tx.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this transaction")
    tx_dict = tx.__dict__.copy()
    tx_dict.pop('_sa_instance_state', None)
    tx_dict['user'] = {
        'id': tx.user.id,
        'username': tx.user.username,
        'email': tx.user.email,
        'role': tx.user.role,
        'is_active': tx.user.is_active,
        'avatar_url': tx.user.avatar_url,
        'firstname': tx.user.firstname,
        'lastname': tx.user.lastname
    } if tx.user else None
    return tx_dict

@router.post("/verify/{transaction_id}", response_model=TransactionInDB)
async def verify_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Verify a pending transaction with Pi Network.
    """
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
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
    tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if tx is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    for field, value in transaction_update.dict(exclude_unset=True).items():
        setattr(tx, field, value)
    db.commit()
    db.refresh(tx)
    return tx

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
    tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if tx is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    db.delete(tx)
    db.commit()
    return {"message": "Transaction deleted successfully"} 