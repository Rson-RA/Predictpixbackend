from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
from typing import List, Optional
from app.models.models import Transaction
from app.schemas.transaction import TransactionCreate, TransactionUpdate, TransactionFilter

def get_transaction(db: Session, transaction_id: int):
    return db.query(Transaction).filter(Transaction.id == transaction_id).first()

def get_transactions(
    db: Session,
    filters: Optional[TransactionFilter] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Transaction]:
    query = db.query(Transaction)
    
    if filters:
        if filters.user_id is not None:
            query = query.filter(Transaction.user_id == filters.user_id)
        if filters.status:
            query = query.filter(Transaction.status == filters.status)
        if filters.start_date and filters.end_date:
            query = query.filter(
                and_(
                    Transaction.created_at >= filters.start_date,
                    Transaction.created_at <= filters.end_date
                )
            )
        elif filters.start_date:
            query = query.filter(Transaction.created_at >= filters.start_date)
        elif filters.end_date:
            query = query.filter(Transaction.created_at <= filters.end_date)

    return query.order_by(Transaction.created_at.desc()).offset(skip).limit(limit).all()

def create_transaction(db: Session, transaction: TransactionCreate):
    db_transaction = Transaction(
        user_id=transaction.user_id,
        amount=transaction.amount,
        status=transaction.status,
        transaction_type=transaction.transaction_type
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

def update_transaction(
    db: Session,
    transaction_id: int,
    transaction_update: TransactionUpdate
):
    db_transaction = get_transaction(db, transaction_id)
    if db_transaction is None:
        return None
        
    update_data = transaction_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_transaction, field, value)
    
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

def delete_transaction(db: Session, transaction_id: int):
    transaction = get_transaction(db, transaction_id)
    if transaction:
        db.delete(transaction)
        db.commit()
    return transaction 