from typing import Dict, List, Tuple
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.models import (
    PredictionMarket,
    Prediction,
    Transaction,
    TransactionType,
    PredictionStatus,
    Reward,
    RewardStatus
)
from datetime import datetime

class RewardCalculator:
    @staticmethod
    def calculate_winner_share(prediction: Prediction, market: PredictionMarket) -> Tuple[Decimal, float]:
        """
        Calculate the winner's share based on their prediction amount and the total pool.
        Returns (reward_amount, reward_multiplier).
        """
        total_pool = Decimal(str(market.total_pool))
        prediction_amount = Decimal(str(prediction.amount))
        
        # Calculate total fees
        total_fee_percentage = Decimal(str(market.platform_fee_percentage + market.creator_fee_percentage))
        fee_multiplier = (100 - total_fee_percentage) / 100
        
        # Calculate the winning pool (amount bet on correct outcome)
        winning_pool = Decimal(str(market.yes_pool if market.correct_outcome == "YES" else market.no_pool))
        
        if winning_pool == 0:
            return Decimal('0'), 0.0
        
        # Calculate proportional share of the total pool after fees
        winner_share = (prediction_amount / winning_pool) * total_pool * fee_multiplier
        reward_multiplier = float(winner_share / prediction_amount) if prediction_amount > 0 else 0.0
        
        return winner_share.quantize(Decimal('.000001')), reward_multiplier

def process_market_rewards(market: PredictionMarket, db: Session) -> List[Transaction]:
    """
    Process rewards for a resolved market and create corresponding transactions and rewards.
    Returns list of created transactions.
    """
    if market.status != "settled" or not market.correct_outcome:
        raise ValueError("Market must be settled with a correct outcome")

    transactions = []
    rewards = []
    
    # Calculate and distribute platform fees
    platform_fee = Decimal(str(market.total_pool)) * Decimal(str(market.platform_fee_percentage)) / 100
    platform_fee_tx = Transaction(
        user_id=1,  # Assuming platform wallet has user_id 1
        type=TransactionType.FEE,
        amount=float(platform_fee),
        status="pending",
        reference_id=f"market_{market.id}_platform_fee",
        metadata={
            "market_id": market.id,
            "fee_type": "platform",
            "percentage": market.platform_fee_percentage
        }
    )
    transactions.append(platform_fee_tx)

    # Calculate and distribute creator fees
    creator_fee = Decimal(str(market.total_pool)) * Decimal(str(market.creator_fee_percentage)) / 100
    creator_fee_tx = Transaction(
        user_id=market.creator_id,
        type=TransactionType.FEE,
        amount=float(creator_fee),
        status="pending",
        reference_id=f"market_{market.id}_creator_fee",
        metadata={
            "market_id": market.id,
            "fee_type": "creator",
            "percentage": market.creator_fee_percentage
        }
    )
    transactions.append(creator_fee_tx)

    # Process winner rewards
    calculator = RewardCalculator()
    winning_predictions = db.query(Prediction).filter(
        Prediction.market_id == market.id,
        Prediction.predicted_outcome == market.correct_outcome
    ).all()

    for prediction in winning_predictions:
        # Calculate winner's share and multiplier
        reward_amount, reward_multiplier = calculator.calculate_winner_share(prediction, market)
        
        # Create winning transaction
        winner_tx = Transaction(
            user_id=prediction.user_id,
            type=TransactionType.WINNINGS,
            amount=float(reward_amount),
            status="pending",
            reference_id=f"market_{market.id}_prediction_{prediction.id}_winnings",
            metadata={
                "market_id": market.id,
                "prediction_id": prediction.id,
                "original_bet": prediction.amount,
                "winning_outcome": market.correct_outcome,
                "reward_multiplier": reward_multiplier
            }
        )
        transactions.append(winner_tx)
        
        # Create reward record
        reward = Reward(
            user_id=prediction.user_id,
            prediction_id=prediction.id,
            market_id=market.id,
            amount=reward_amount,
            original_prediction_amount=prediction.amount,
            reward_multiplier=reward_multiplier,
            status=RewardStatus.PENDING,
            metadata={
                "market_title": market.title,
                "winning_outcome": market.correct_outcome,
                "total_pool": float(market.total_pool),
                "winning_pool": float(market.yes_pool if market.correct_outcome == "YES" else market.no_pool),
                "fees": {
                    "platform": market.platform_fee_percentage,
                    "creator": market.creator_fee_percentage
                },
                "calculated_at": datetime.utcnow().isoformat()
            }
        )
        rewards.append(reward)
        
        # Update prediction status
        prediction.status = PredictionStatus.WON
        prediction.potential_winnings = float(reward_amount)

    # Update losing predictions
    db.query(Prediction).filter(
        Prediction.market_id == market.id,
        Prediction.predicted_outcome != market.correct_outcome
    ).update({"status": PredictionStatus.LOST})

    # Add all transactions and rewards to database
    db.add_all(transactions)
    db.add_all(rewards)
    
    # Link rewards to transactions
    for reward, transaction in zip(rewards, [tx for tx in transactions if tx.type == TransactionType.WINNINGS]):
        reward.transaction_id = transaction.id
    
    db.commit()

    return transactions

async def execute_pi_payment(transaction: Transaction, db: Session) -> bool:
    """
    Execute a PI payment transaction.
    Returns True if successful, False otherwise.
    """
    try:
        # TODO: Implement actual PI Network payment API integration
        # This is a placeholder for the actual PI Network payment implementation
        
        # Update transaction status
        transaction.status = "completed"
        transaction.metadata = {
            **transaction.metadata,
            "completed_at": datetime.utcnow().isoformat(),
            "payment_processor": "pi_network"
        }
        
        # Update associated reward if exists
        if transaction.reward:
            transaction.reward.status = RewardStatus.PROCESSED
            transaction.reward.processed_at = datetime.utcnow()
        
        # Update user balance
        user = transaction.user
        if transaction.type in [TransactionType.WINNINGS, TransactionType.REFUND]:
            user.balance += transaction.amount
        elif transaction.type == TransactionType.PREDICTION:
            user.balance -= transaction.amount
        
        db.commit()
        return True
        
    except Exception as e:
        transaction.status = "failed"
        transaction.metadata = {
            **transaction.metadata,
            "error": str(e),
            "failed_at": datetime.utcnow().isoformat()
        }
        
        # Update associated reward status if exists
        if transaction.reward:
            transaction.reward.status = RewardStatus.FAILED
        
        db.commit()
        return False

async def process_pending_transactions(db: Session) -> Dict[str, int]:
    """
    Process all pending transactions.
    Returns statistics about processed transactions.
    """
    stats = {
        "total": 0,
        "successful": 0,
        "failed": 0
    }
    
    pending_transactions = db.query(Transaction).filter(
        Transaction.status == "pending"
    ).all()
    
    stats["total"] = len(pending_transactions)
    
    for transaction in pending_transactions:
        success = await execute_pi_payment(transaction, db)
        if success:
            stats["successful"] += 1
        else:
            stats["failed"] += 1
    
    return stats 