from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from app.core.config import settings
from app.core.database import db
from app.api.v1 import videos

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create API router
api_router = APIRouter()
api_router.include_router(videos.router, tags=["videos"])

# Include API router in app
app.include_router(api_router, prefix=settings.API_V1_STR)


# Root endpoint
@app.get("/")
async def root():
    return {
        "status": "online",
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# Events for database connection
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up VidRead API...")
    await db.connect()
    logger.info("VidRead API started!")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down VidRead API...")
    await db.close()
    logger.info("VidRead API shutdown complete!")


# Exception handlers
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": f"An unexpected error occurred: {str(exc)}"},
    )


# Start the application with: uvicorn app.main:app --reload
# Documentation available at: http://localhost:8000/docs