from fastapi import FastAPI, APIRouter, HTTPException, Depends, BackgroundTasks, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, HttpUrl
from datetime import datetime

from app.core.config import settings
from app.core.database import db
from app.services.video import VideoService

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="YTBook",
    description="YouTube to Book Conversion API",
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

# Initialize services
video_service = VideoService()

# Define API models
class VideoUrlInput(BaseModel):
    url: HttpUrl


class ProcessingResponse(BaseModel):
    message: str
    status: str
    task_id: Optional[str] = None


class BookSearchParams(BaseModel):
    query: Optional[str] = None
    difficulty: Optional[str] = None
    skip: int = 0
    limit: int = 10


# Create API router
api_router = APIRouter()


# Endpoints
@api_router.post("/process", response_model=ProcessingResponse)
async def process_video(
    background_tasks: BackgroundTasks,
    input_data: VideoUrlInput
):
    """
    Start processing a YouTube video to convert it into book format.
    """
    try:
        # Generate a task ID
        task_id = f"task-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Start background processing task
        background_tasks.add_task(
            video_service.process_video,
            str(input_data.url)
        )
        
        return {
            "message": "Processing started",
            "status": "pending",
            "task_id": task_id
        }
    except Exception as e:
        logger.error(f"Error starting processing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error starting processing: {str(e)}")


@api_router.get("/books/{book_id}")
async def get_book(book_id: str):
    """
    Get a processed book by ID.
    """
    try:
        book = await video_service.get_book_by_id(book_id)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        return book
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting book: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving book: {str(e)}")


@api_router.get("/books")
async def search_books(
    query: Optional[str] = None,
    difficulty: Optional[str] = None,
    skip: int = 0,
    limit: int = 10
):
    """
    Search for books with various filters.
    """
    try:
        books = await video_service.search_books(
            query=query,
            difficulty=difficulty,
            skip=skip,
            limit=limit
        )
        return books
    except Exception as e:
        logger.error(f"Error searching books: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching books: {str(e)}")


# Include API router in app
app.include_router(api_router, prefix=settings.API_V1_STR)


# Root endpoint
@app.get("/")
async def root():
    return {
        "status": "online",
        "name": "YTBook API",
        "version": settings.VERSION,
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# Events for database connection
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up YTBook API...")
    await db.connect()
    
    # Set up text search indexes
    try:
        await db.db.books.create_index([
            ("title", "text"),
            ("summary", "text"),
            ("key_themes", "text")
        ])
        logger.info("Created text search indexes")
    except Exception as e:
        logger.error(f"Error creating indexes: {str(e)}")
    
    logger.info("YTBook API started!")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down YTBook API...")
    await db.close()
    logger.info("YTBook API shutdown complete!")


# Exception handlers
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": f"An unexpected error occurred: {str(exc)}"},
    )