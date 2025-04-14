from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Enum, JSON, Text, DateTime, Numeric
from sqlalchemy.orm import relationship
from app.models.base import Base
import enum
from datetime import datetime

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"

class MarketType(str, enum.Enum):
    BINARY = "binary"
    MULTIPLE = "multiple"

class MarketStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    CLOSED = "closed"
    SETTLED = "settled"
    CANCELLED = "cancelled"

class PredictionStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    WON = "won"
    LOST = "lost"
    CANCELLED = "cancelled"

class TransactionType(str, enum.Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    PREDICTION = "prediction"
    WINNINGS = "winnings"
    REFUND = "refund"
    FEE = "fee"

class RewardStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    pi_user_id = Column(String, unique=True, index=True, nullable=True)  # Allow null for email-based registration
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    phone_number = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=True)  # Only required for admin users
    avatar_url = Column(String, nullable=True)  # URL to user's avatar image
    role = Column(Enum(UserRole), default=UserRole.USER)
    balance = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    predictions = relationship("Prediction", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")
    created_markets = relationship("PredictionMarket", back_populates="creator")
    rewards = relationship("Reward", back_populates="user")

class PredictionMarket(Base):
    __tablename__ = "prediction_markets"
    
    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, nullable=False)
    description = Column(Text)
    end_time = Column(DateTime, nullable=False)
    resolution_time = Column(DateTime, nullable=False)
    status = Column(Enum(MarketStatus), default=MarketStatus.PENDING)
    total_pool = Column(Float, default=0.0)
    yes_pool = Column(Float, default=0.0)  # Total amount bet on YES
    no_pool = Column(Float, default=0.0)   # Total amount bet on NO
    correct_outcome = Column(String)  # Will be either "YES" or "NO"
    creator_fee_percentage = Column(Float, default=1.0)
    platform_fee_percentage = Column(Float, default=2.0)
    market_metadata = Column(JSON)
    
    # Relationships
    creator = relationship("User", back_populates="created_markets")
    predictions = relationship("Prediction", back_populates="market")
    rewards = relationship("Reward", back_populates="market")

class Prediction(Base):
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    market_id = Column(Integer, ForeignKey("prediction_markets.id"))
    amount = Column(Float, nullable=False)
    predicted_outcome = Column(String, nullable=False)  # Will be either "YES" or "NO"
    status = Column(Enum(PredictionStatus), default=PredictionStatus.PENDING)
    potential_winnings = Column(Float)
    
    # Relationships
    user = relationship("User", back_populates="predictions")
    market = relationship("PredictionMarket", back_populates="predictions")
    reward = relationship("Reward", back_populates="prediction", uselist=False)

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(Enum(TransactionType))
    amount = Column(Float, nullable=False)
    status = Column(String)  # pending, completed, failed
    tx_hash = Column(String)  # Pi Network transaction hash
    reference_id = Column(String)  # Reference to prediction/market ID
    transaction_metadata = Column(JSON)
    
    # Relationships
    user = relationship("User", back_populates="transactions")
    reward = relationship("Reward", back_populates="transaction", uselist=False)

class Reward(Base):
    __tablename__ = "rewards"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    prediction_id = Column(Integer, ForeignKey("predictions.id"), nullable=False)
    market_id = Column(Integer, ForeignKey("prediction_markets.id"), nullable=False)
    amount = Column(Numeric(precision=20, scale=6), nullable=False)
    original_prediction_amount = Column(Numeric(precision=20, scale=6), nullable=False)
    reward_multiplier = Column(Float, nullable=False)
    status = Column(Enum(RewardStatus), nullable=False, default=RewardStatus.PENDING)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    reward_metadata = Column(JSON, nullable=True)

    # Relationships
    user = relationship("User", back_populates="rewards")
    prediction = relationship("Prediction", back_populates="reward")
    market = relationship("PredictionMarket", back_populates="rewards")
    transaction = relationship("Transaction", back_populates="reward") 