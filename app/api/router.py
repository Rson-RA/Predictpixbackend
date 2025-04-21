from fastapi import APIRouter
from app.api import auth, users, markets, predictions, admin, referral, transactions, rewards

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(markets.router)
api_router.include_router(predictions.router)
api_router.include_router(transactions.router)
api_router.include_router(rewards.router)
api_router.include_router(admin.router)
api_router.include_router(referral.router) 