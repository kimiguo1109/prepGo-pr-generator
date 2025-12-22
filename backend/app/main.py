"""FastAPI application entry point for Practice Generator with multi-user support."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import settings
from app.services.course_service import CourseService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting PrepGo Practice Generator...")
    
    # Preload course data for faster response times
    logger.info("Preloading course data...")
    CourseService.preload_courses()
    
    logger.info("Application started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down PrepGo Practice Generator...")


app = FastAPI(
    title="PrepGo Practice Generator",
    description="Generate customizable AP practice sets with AI - Supports multiple concurrent users",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware - configure for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://react.prepgo.com",
        "http://react.prepgo.com",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "app": "PrepGo Practice Generator",
        "version": "1.0.0",
        "docs": "/docs",
        "features": [
            "Multi-unit selection",
            "Customizable MCQ/FRQ counts",
            "Difficulty levels",
            "Multi-user concurrent support",
            "Queue management"
        ]
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    from app.services.queue_manager import QueueManager
    from app.services.gemini_client import GeminiClient
    
    queue_status = await QueueManager.get_queue_status()
    cache_stats = CourseService.get_cache_stats()
    gemini_stats = GeminiClient.get_stats()
    
    return {
        "status": "healthy",
        "queue": queue_status,
        "cache": cache_stats,
        "gemini": gemini_stats
    }


@app.get("/stats")
async def stats():
    """Get detailed system statistics."""
    from app.services.queue_manager import QueueManager
    from app.services.gemini_client import GeminiClient
    
    queue_status = await QueueManager.get_detailed_status()
    cache_stats = CourseService.get_cache_stats()
    gemini_stats = GeminiClient.get_stats()
    
    return {
        "queue": queue_status,
        "cache": cache_stats,
        "gemini": gemini_stats
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host=settings.host, 
        port=settings.port,
        workers=1,  # Use 1 worker for async - scale with multiple instances instead
        log_level="info"
    )
