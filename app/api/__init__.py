from app.api.markets import router as markets_router
from app.api.predictions import router as predictions_router
from app.api.auth import router as users_router  # auth module handles user endpoints
from app.api.admin import router as admin_router

# Export the routers directly
markets = markets_router
users = users_router
predictions = predictions_router
admin = admin_router

__all__ = ["markets", "users", "predictions", "admin"] 