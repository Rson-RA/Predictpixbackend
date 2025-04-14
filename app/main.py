from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.core.middleware import RateLimitMiddleware
from app.api import markets, predictions, admin, users
from app.api.auth import router as auth_router
from app.db.session import get_db
from app.db.utils import init_db
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Cryptocurrency prediction betting platform powered by Pi Network"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Create static directory if it doesn't exist
os.makedirs("static/avatars", exist_ok=True)

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers with prefixes
app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])
app.include_router(markets, prefix="/api/markets", tags=["markets"])
app.include_router(predictions, prefix="/api/predictions", tags=["predictions"])
app.include_router(admin, prefix="/api/admin", tags=["admin"])
app.include_router(users, prefix="/api/users", tags=["users"])

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    try:
        # Initialize database (create admin user)
        db = next(get_db())
        init_db(db)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise

@app.get("/")
async def root():
    return {"message": "Welcome to PredictPix - Cryptocurrency Prediction Platform"} 