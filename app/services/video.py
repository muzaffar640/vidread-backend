from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import re
import uuid
import modal
from bson import ObjectId
from app.core.database import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import Modal functions
from app.services.modal_functions import extract_audio, transcribe_audio, process_transcript


class VideoService:
    """Service for video processing pipeline."""
    
    def __init__(self):
        # We don't need to instantiate a Modal client explicitly
        # The remote functions are imported through modal_functions.py
        pass
    
    def _extract_video_id(self, video_url: str) -> str:
        """Extract video ID from YouTube URL."""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/|youtube\.com\/watch\?.*v=|youtube\.com\/watch\?.*&v=)([^&\n?#]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, video_url)
            if match:
                return match.group(1)
                
        raise ValueError(f"Could not extract video ID from URL: {video_url}")
    
    async def process_video(self, video_url: str, use_modal: bool = True) -> Dict[str, Any]:
        """
        Process a YouTube video through the entire pipeline.
        
        Args:
            video_url: YouTube video URL
            use_modal: Whether to use Modal for processing
            
        Returns:
            Processed book content
        """
        try:
            logger.info(f"Starting processing for video: {video_url}")
            video_id = self._extract_video_id(video_url)
            
            # Check if video already exists in database
            existing_book = await db.db.books.find_one({"source_video.id": video_id})
            if existing_book:
                logger.info(f"Video already processed: {video_id}")
                existing_book["_id"] = str(existing_book["_id"])
                return existing_book
            
            # Start the processing pipeline
            if use_modal:
                # Extract audio using Modal
                logger.info("Extracting audio with Modal")
                audio_result = extract_audio.remote(video_url)
                metadata = audio_result["metadata"]
                audio_bytes = audio_result["audio_bytes"]
                
                # Transcribe audio using Modal
                logger.info("Transcribing audio with Modal")
                transcription_result = transcribe_audio.remote(audio_bytes, metadata)
                transcript = transcription_result["transcript"]
                
                # Process content using Modal
                logger.info("Processing content with Modal")
                book_content = process_transcript.remote(transcript, metadata)
                
            else:
                # Local processing or fallback (simplified)
                logger.info("Modal processing unavailable, using fallback")
                raise NotImplementedError("Local processing not implemented yet")
            
            # Prepare for database storage
            book_document = {
                **book_content,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "processing_status": "completed"
            }
            
            # Save to database
            result = await db.db.books.insert_one(book_document)
            book_document["_id"] = str(result.inserted_id)
            
            logger.info(f"Video successfully processed and saved: {video_id}")
            return book_document
            
        except Exception as e:
            logger.error(f"Error processing video: {str(e)}")
            
            # Create error entry in database
            error_doc = {
                "video_url": video_url,
                "error": str(e),
                "created_at": datetime.utcnow(),
                "processing_status": "failed"
            }
            
            try:
                await db.db.processing_errors.insert_one(error_doc)
            except Exception as db_err:
                logger.error(f"Error saving error document: {str(db_err)}")
                
            raise
    
    async def get_book_by_id(self, book_id: str) -> Optional[Dict[str, Any]]:
        """Get a book by its ID."""
        try:
            book = await db.db.books.find_one({"_id": ObjectId(book_id)})
            if book:
                book["_id"] = str(book["_id"])
            return book
        except Exception as e:
            logger.error(f"Error getting book by ID: {str(e)}")
            return None
    
    async def search_books(self, 
                          query: Optional[str] = None,
                          difficulty: Optional[str] = None,
                          skip: int = 0, 
                          limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for books with various filters.
        
        Args:
            query: Text search query
            difficulty: Filter by difficulty level
            skip: Number of results to skip
            limit: Maximum number of results to return
            
        Returns:
            List of matching books
        """
        try:
            # Build the search filter
            filter_dict = {}
            
            if difficulty:
                filter_dict["difficulty_level"] = difficulty
            
            if query:
                # Text search
                text_filter = {"$text": {"$search": query}}
                
                if filter_dict:
                    # Combine text search with other filters
                    filter_dict = {"$and": [filter_dict, text_filter]}
                else:
                    filter_dict = text_filter
                    
                # Use text score for sorting
                cursor = db.db.books.find(
                    filter_dict,
                    {"score": {"$meta": "textScore"}}
                ).sort([("score", {"$meta": "textScore"})])
            else:
                # No text search, use regular filter and sort by creation date
                cursor = db.db.books.find(filter_dict).sort("created_at", -1)
            
            # Apply pagination
            cursor = cursor.skip(skip).limit(limit)
            
            # Get results
            books = []
            async for book in cursor:
                book["_id"] = str(book["_id"])
                books.append(book)
                
            return books
            
        except Exception as e:
            logger.error(f"Error searching books: {str(e)}")
            return []