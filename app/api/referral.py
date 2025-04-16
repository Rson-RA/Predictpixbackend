from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
import secrets
import string
from app.core.deps import get_db, get_current_user
from app.models.models import User, ReferralTransaction, Transaction, TransactionType, TransactionStatus
from app.schemas.referral import ReferralResponse, ReferralStats, ReferralTransactionResponse
from app.core.config import settings

router = APIRouter()

def generate_referral_code(length: int = 8) -> str:
    """Generate a random referral code."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

@router.get("/my-referral", response_model=ReferralResponse)
def get_my_referral(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's referral information."""
    # Generate referral code if not exists
    if not current_user.referral_code:
        while True:
            referral_code = generate_referral_code()
            exists = db.query(User).filter(User.referral_code == referral_code).first()
            if not exists:
                current_user.referral_code = referral_code
                db.commit()
                break

    total_referrals = db.query(User).filter(User.referred_by_id == current_user.id).count()
    referred_by = None
    if current_user.referred_by_id:
        referred_by = db.query(User).filter(User.id == current_user.referred_by_id).first()

    return {
        "referral_code": current_user.referral_code,
        "referral_url": f"{settings.FRONTEND_URL}/register?ref={current_user.referral_code}",
        "referral_earnings": current_user.referral_earnings,
        "total_referrals": total_referrals,
        "referred_by": referred_by
    }

@router.get("/stats", response_model=ReferralStats)
def get_referral_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's referral statistics."""
    total_referrals = db.query(User).filter(User.referred_by_id == current_user.id).count()
    
    recent_referrals = (
        db.query(ReferralTransaction)
        .filter(ReferralTransaction.user_id == current_user.id)
        .order_by(ReferralTransaction.created_at.desc())
        .limit(10)
        .all()
    )
    
    return {
        "total_referrals": total_referrals,
        "total_earnings": current_user.referral_earnings,
        "recent_referrals": recent_referrals
    }

@router.get("/transactions", response_model=List[ReferralTransactionResponse])
def get_referral_transactions(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's referral transactions."""
    transactions = (
        db.query(ReferralTransaction)
        .filter(ReferralTransaction.user_id == current_user.id)
        .order_by(ReferralTransaction.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return transactions

async def process_referral(
    db: Session,
    referred_user: User,
    referrer: User,
    amount: float = settings.REFERRAL_BONUS_AMOUNT
):
    """Process a referral and create necessary transactions."""
    # Create a transaction for the referral bonus
    transaction = Transaction(
        user_id=referrer.id,
        amount=amount,
        status=TransactionStatus.COMPLETED,
        transaction_type=TransactionType.REFERRAL,
        transaction_metadata={"referred_user_id": referred_user.id}
    )
    db.add(transaction)
    db.flush()  # Get transaction ID

    # Create referral transaction record
    referral_tx = ReferralTransaction(
        user_id=referrer.id,
        referred_user_id=referred_user.id,
        amount=amount,
        transaction_id=transaction.id
    )
    db.add(referral_tx)

    # Update referrer's earnings
    referrer.referral_earnings += amount
    referrer.balance += amount

    db.commit() 