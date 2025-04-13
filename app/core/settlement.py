from typing import List, Dict
from sqlalchemy.orm import Session
from app.models.models import PredictionMarket, Prediction, Transaction, TransactionType, PredictionStatus
from decimal import Decimal, ROUND_DOWN
from datetime import datetime

class MarketSettlement:
    def __init__(self, market: PredictionMarket, db: Session):
        self.market = market
        self.db = db
        self.total_pool = Decimal(str(market.total_pool))
        self.platform_fee = Decimal(str(market.platform_fee_percentage)) / Decimal('100')
        self.creator_fee = Decimal(str(market.creator_fee_percentage)) / Decimal('100')
        self.winning_pool = Decimal('0')
        self.total_fees = Decimal('0')
        self.predictions_by_outcome: Dict[str, List[Prediction]] = {}

    def process_settlement(self) -> None:
        """
        Process the settlement for a resolved market.
        """
        # Group predictions by outcome
        self._group_predictions()
        
        # Calculate winning pool
        self.winning_pool = sum(
            Decimal(str(pred.amount))
            for pred in self.predictions_by_outcome.get(self.market.correct_outcome, [])
        )
        
        # Calculate fees
        self.total_fees = self.total_pool * (self.platform_fee + self.creator_fee)
        distributable_pool = self.total_pool - self.total_fees
        
        # Process winning predictions
        if self.winning_pool > 0:
            self._process_winning_predictions(distributable_pool)
        
        # Process losing predictions
        self._process_losing_predictions()
        
        # Distribute fees
        self._distribute_fees()

    def _group_predictions(self) -> None:
        """
        Group all predictions by their predicted outcome.
        """
        for prediction in self.market.predictions:
            if prediction.predicted_outcome not in self.predictions_by_outcome:
                self.predictions_by_outcome[prediction.predicted_outcome] = []
            self.predictions_by_outcome[prediction.predicted_outcome].append(prediction)

    def _process_winning_predictions(self, distributable_pool: Decimal) -> None:
        """
        Process and distribute winnings to correct predictions.
        """
        for prediction in self.predictions_by_outcome.get(self.market.correct_outcome, []):
            # Calculate winnings proportional to contribution
            contribution_ratio = Decimal(str(prediction.amount)) / self.winning_pool
            winnings = (distributable_pool * contribution_ratio).quantize(Decimal('0.00000001'), rounding=ROUND_DOWN)
            
            # Update prediction status and winnings
            prediction.status = PredictionStatus.WON
            prediction.potential_winnings = float(winnings)
            
            # Create winning transaction
            self._create_winning_transaction(prediction, winnings)
            
            # Update user balance
            prediction.user.balance += float(winnings)

    def _process_losing_predictions(self) -> None:
        """
        Update status for losing predictions.
        """
        for outcome, predictions in self.predictions_by_outcome.items():
            if outcome != self.market.correct_outcome:
                for prediction in predictions:
                    prediction.status = PredictionStatus.LOST
                    prediction.potential_winnings = 0

    def _distribute_fees(self) -> None:
        """
        Distribute platform and creator fees.
        """
        # Calculate fee amounts
        platform_fee_amount = self.total_pool * self.platform_fee
        creator_fee_amount = self.total_pool * self.creator_fee
        
        # Create platform fee transaction
        self._create_fee_transaction(
            amount=float(platform_fee_amount),
            fee_type="platform",
            recipient_id=None  # Platform fee goes to treasury
        )
        
        # Create creator fee transaction
        self._create_fee_transaction(
            amount=float(creator_fee_amount),
            fee_type="creator",
            recipient_id=self.market.creator_id
        )
        
        # Update creator balance
        creator = self.market.creator
        if creator:
            creator.balance += float(creator_fee_amount)

    def _create_winning_transaction(self, prediction: Prediction, amount: Decimal) -> None:
        """
        Create a transaction record for prediction winnings.
        """
        transaction = Transaction(
            user_id=prediction.user_id,
            type=TransactionType.WINNINGS,
            amount=float(amount),
            status="completed",
            reference_id=f"market_{self.market.id}_prediction_{prediction.id}",
            metadata={
                "market_id": self.market.id,
                "prediction_id": prediction.id,
                "winning_outcome": self.market.correct_outcome
            }
        )
        self.db.add(transaction)

    def _create_fee_transaction(self, amount: float, fee_type: str, recipient_id: int | None) -> None:
        """
        Create a transaction record for fee distribution.
        """
        transaction = Transaction(
            user_id=recipient_id if recipient_id else None,
            type=TransactionType.FEE,
            amount=amount,
            status="completed",
            reference_id=f"market_{self.market.id}_fee_{fee_type}",
            metadata={
                "market_id": self.market.id,
                "fee_type": fee_type,
                "fee_percentage": float(self.platform_fee if fee_type == "platform" else self.creator_fee)
            }
        )
        self.db.add(transaction)

def process_market_settlement(market: PredictionMarket, db: Session) -> None:
    """
    Main function to process market settlement.
    """
    if not market.correct_outcome:
        raise ValueError("Market must have a correct outcome set")
    
    settlement = MarketSettlement(market, db)
    settlement.process_settlement()
    
    # Commit all changes
    db.commit() 