from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.base import STATE_STOPPED
import datetime
from app.core.config import settings
from app.core.middleware import RateLimitMiddleware
from app.api import api_router
from app.db.session import get_db
from app.db.utils import init_db
import logging
import os
from dotenv import load_dotenv
from app.core.jobs import resolve_due_markets, close_expired_markets
from app.core.socket import SocketManager

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

scheduler = BackgroundScheduler()

# CORS middleware configuration with explicit origins
origins = [
    "http://152.42.252.223:8000",  # Public IP
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:8081",
    "http://localhost:3000",
    "http://localhost:5173",  # Vite default port
    "http://127.0.0.1:5173",
    "http://localhost",
    "http://127.0.0.1",
    "http://10.0.2.2:8081",
    "http://10.0.2.2:3000",
    "http://10.0.2.2:5173",
    "http://10.0.2.2:8000"
]

# Add any additional origins from settings
if settings.ALLOWED_ORIGINS:
    origins.extend(settings.ALLOWED_ORIGINS)

# CORS middleware must be first to handle preflight requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Rate limiting middleware comes after CORS
app.add_middleware(RateLimitMiddleware)

# Include API router first
app.include_router(api_router, prefix=settings.API_V1_STR)

# Create static directory if it doesn't exist
os.makedirs("upload/avatars", exist_ok=True)

# Mount static files directory for user uploads
app.mount("/upload", StaticFiles(directory="upload"), name="upload")

# Mount React static files last
app.mount("/static", StaticFiles(directory="admin/build/static"), name="static")

# app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    user_id = websocket.query_params.get("user_id")
    socket_manager = SocketManager()
    await socket_manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        print("Client disconnected")

def check_unresolved_markets():
    print(f"[{datetime.datetime.now()}] Checking unresolved markets...")
    # Add logic here: check markets, resolve if needed, push updates
    resolve_due_markets()
    close_expired_markets()

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    try:
        # Initialize database (create admin user)
        db = next(get_db())
        init_db(db)
        logger.info("Database initialized successfully")
        
        # Start the scheduler if it's not already running
        # if scheduler.state == STATE_STOPPED:
        #     scheduler.add_job(check_unresolved_markets, "interval", seconds=10)
        #     scheduler.start()
            # logger.info("Scheduler started successfully")
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    try:
        # Only attempt to shut down if the scheduler is running
        if scheduler.state != STATE_STOPPED:
            scheduler.shutdown(wait=False)
            logger.info("Scheduler stopped successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")
        # Don't raise the exception during shutdown to allow clean exit
        pass
    
# Serve static React files
# @app.get("/app")
# async def get_react_app():
#     # Return the index.html from the React build folder
#     return FileResponse(os.path.join("frontend", "dist", "index.html"))

@app.get("/")
async def get_admin_app():
    # Return the index.html from the React build folder
    return FileResponse(os.path.join("admin", "build", "index.html"))

# # Serve static files (JS, CSS, etc.)
# @app.get("/static/{file_path:path}")
# async def serve_static(type: str, file_path: str):
#     logger.info(f"Serving static file: {file_path}")
#     return FileResponse(os.path.join("admin", "build", "static", type, file_path))

# # Serve assets files (JS, CSS, etc.)
# @app.get("/assets/{file_path:path}")
# async def serve_assets(type: str, file_path: str):
#     logger.info(f"Serving static file: {file_path}")
#     return FileResponse(os.path.join("frontend", "dist", "assets", type, file_path))