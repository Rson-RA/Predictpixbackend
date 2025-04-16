from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.core.config import settings
from app.core.middleware import RateLimitMiddleware
from app.api import api_router
from app.db.session import get_db
from app.db.utils import init_db
import logging
import os
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Cryptocurrency prediction betting platform powered by Pi Network",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
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

# Include API router first
app.include_router(api_router, prefix=settings.API_V1_STR)

# Create static directory if it doesn't exist
os.makedirs("upload/avatars", exist_ok=True)

# Mount static files directory for user uploads
app.mount("/upload", StaticFiles(directory="upload"), name="upload")

# Mount React static files last
# app.mount("/", StaticFiles(directory="frontend/build", html=True), name="static")

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

# Serve static React files
@app.get("/")
async def get_react_app():
    # Return the index.html from the React build folder
    return FileResponse(os.path.join("frontend", "build", "index.html"))

# # Serve static files (JS, CSS, etc.)
@app.get("/static/{file_path:path}")
async def serve_static(type: str, file_path: str):
    logger.info(f"Serving static file: {file_path}")
    return FileResponse(os.path.join("frontend", "build", "static", type, file_path))