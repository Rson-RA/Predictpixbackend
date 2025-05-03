from datetime import datetime, timezone
from app.db.session import SessionLocal
from app.models.models import PredictionMarket, MarketStatus
from app.core.settlement import process_market_settlement
from app.core.config import settings

def close_expired_markets():
    """
    Find all ACTIVE markets whose end_time has passed and set them to CLOSED.
    """
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        markets = db.query(PredictionMarket).filter(
            PredictionMarket.status == MarketStatus.ACTIVE,
            PredictionMarket.end_time <= now
        ).all()
        for market in markets:
            market.status = MarketStatus.CLOSED
        db.commit()
    finally:
        db.close()

def resolve_due_markets():
    """
    Find all CLOSED markets whose resolution_time has passed and have a correct_outcome, and process settlement.
    """
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        markets = db.query(PredictionMarket).filter(
            PredictionMarket.status == MarketStatus.CLOSED,
            PredictionMarket.resolution_time <= now,
            PredictionMarket.correct_outcome.isnot(None)
        ).all()
        for market in markets:
            process_market_settlement(market, db)
            market.status = MarketStatus.SETTLED
        db.commit()
    finally:
        db.close()

# To schedule these tasks, configure Celery beat in your worker setup. 