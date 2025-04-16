from fastapi import APIRouter
from app.api import transactions, markets, auth, users, admin, rewards, predictions, referral

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(markets.router, prefix="/markets", tags=["markets"])
api_router.include_router(predictions.router, prefix="/predictions", tags=["predictions"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
api_router.include_router(rewards.router, prefix="/rewards", tags=["rewards"])
api_router.include_router(referral.router, prefix="/referral", tags=["referral"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])

__all__ = ["api_router"] 