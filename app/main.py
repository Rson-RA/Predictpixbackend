from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.middleware import RateLimitMiddleware
from app.api import markets, predictions, admin
from app.api.auth import router as auth_router
from app.db.session import get_db
from app.db.utils import init_db
import logging

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

# Include routers with prefixes
app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])
app.include_router(markets, prefix="/markets", tags=["markets"])
app.include_router(predictions, prefix="/predictions", tags=["predictions"])
app.include_router(admin, prefix="/admin", tags=["admin"])

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