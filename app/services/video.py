from datetime import datetime
from typing import Dict, Any, List, Optional
from bson import ObjectId
import logging
from app.core.database import db
from app.services.youtube import YouTubeService
from app.services.ai import AIProcessingService
from app.models.video import VideoCreate, VideoInDB, VideoUpdate, VideoResponse

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VideoService:
    """Service for video processing and database operations."""
    
    def __init__(self):
        self.youtube_service = YouTubeService()
        self.ai_service = AIProcessingService()
        
    async def process_video_url(self, video_url: str) -> Dict[str, Any]:
        """
        Process a YouTube video URL to extract and enhance content.
        
        Args:
            video_url: YouTube video URL
            
        Returns:
            Processed video data
        """
        try:
            logger.info(f"Processing video URL: {video_url}")
            
            # Extract video details from YouTube
            video_data = await self.youtube_service.get_video_details(video_url)
            
            # Get video transcript
            video_id = video_data["video_id"]
            transcript = await self.youtube_service.get_transcript(video_id)
            
            if transcript:
                logger.info(f"Transcript retrieved for video {video_id}, length: {len(transcript)} chars")
            else:
                logger.warning(f"No transcript available for video {video_id}")
            
            # Process with AI
            enhanced_data = await self.ai_service.process_video_content(video_data, transcript)
            
            return enhanced_data
            
        except Exception as e:
            logger.error(f"Error processing video URL: {str(e)}")
            raise
    
    async def create_video(self, video_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new video document in the database.
        
        Args:
            video_data: Processed video data
            
        Returns:
            Created video document with ID
        """
        try:
            # Add timestamps
            now = datetime.utcnow()
            video_data["created_at"] = now
            video_data["updated_at"] = now
            
            # Insert into database
            result = await db.db.videos.insert_one(video_data)
            
            # Get the created document
            created_video = await db.db.videos.find_one({"_id": result.inserted_id})
            
            # Convert ObjectId to string for the response
            created_video["_id"] = str(created_video["_id"])
            
            return created_video
            
        except Exception as e:
            logger.error(f"Error creating video in database: {str(e)}")
            raise
    
    async def get_video_by_id(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a video by its ID.
        
        Args:
            video_id: Video document ID
            
        Returns:
            Video document or None if not found
        """
        try:
            video = await db.db.videos.find_one({"_id": ObjectId(video_id)})
            
            if video:
                # Convert ObjectId to string
                video["_id"] = str(video["_id"])
                
            return video
            
        except Exception as e:
            logger.error(f"Error getting video by ID: {str(e)}")
            return None
    
    async def get_video_by_youtube_id(self, youtube_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a video by its YouTube ID.
        
        Args:
            youtube_id: YouTube video ID
            
        Returns:
            Video document or None if not found
        """
        try:
            video = await db.db.videos.find_one({"video_id": youtube_id})
            
            if video:
                # Convert ObjectId to string
                video["_id"] = str(video["_id"])
                
            return video
            
        except Exception as e:
            logger.error(f"Error getting video by YouTube ID: {str(e)}")
            return None
    
    async def get_videos(self, 
                         skip: int = 0, 
                         limit: int = 10, 
                         category: Optional[str] = None,
                         tags: Optional[List[str]] = None,
                         search: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get videos with filtering options.
        
        Args:
            skip: Number of documents to skip
            limit: Maximum number of documents to return
            category: Filter by category
            tags: Filter by tags
            search: Text search query
            
        Returns:
            List of video documents
        """
        try:
            # Build the query
            query = {}
            
            if category:
                query["library_data.categories"] = category
                
            if tags:
                query["library_data.tags"] = {"$all": tags}
                
            if search:
                # Use text search if a search query is provided
                cursor = db.db.videos.find(
                    {"$text": {"$search": search}},
                    {"score": {"$meta": "textScore"}}
                ).sort([("score", {"$meta": "textScore"})])
            else:
                # Otherwise, use the regular query and sort by creation date
                cursor = db.db.videos.find(query).sort("created_at", -1)
            
            # Apply pagination
            cursor = cursor.skip(skip).limit(limit)
            
            # Convert cursor to list
            videos = []
            async for video in cursor:
                # Convert ObjectId to string
                video["_id"] = str(video["_id"])
                videos.append(video)
                
            return videos
            
        except Exception as e:
            logger.error(f"Error getting videos: {str(e)}")
            return []
            
    async def update_video(self, video_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a video document.
        
        Args:
            video_id: Video document ID
            update_data: Data to update
            
        Returns:
            Updated video document or None if not found
        """
        try:
            # Add updated timestamp
            update_data["updated_at"] = datetime.utcnow()
            
            # Update the document
            result = await db.db.videos.update_one(
                {"_id": ObjectId(video_id)},
                {"$set": update_data}
            )
            
            if result.modified_count == 0:
                logger.warning(f"No video updated with ID: {video_id}")
                return None
                
            # Get the updated document
            updated_video = await db.db.videos.find_one({"_id": ObjectId(video_id)})
            
            if updated_video:
                # Convert ObjectId to string
                updated_video["_id"] = str(updated_video["_id"])
                
            return updated_video
            
        except Exception as e:
            logger.error(f"Error updating video: {str(e)}")
            return None
            
    async def delete_video(self, video_id: str) -> bool:
        """
        Delete a video document.
        
        Args:
            video_id: Video document ID
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            result = await db.db.videos.delete_one({"_id": ObjectId(video_id)})
            
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting video: {str(e)}")
            return False
    
    async def process_and_save_video(self, video_url: str) -> Dict[str, Any]:
        """
        Process a YouTube video URL and save it to the database.
        
        Args:
            video_url: YouTube video URL
            
        Returns:
            Processed and saved video document
        """
        try:
            # Check if the video already exists
            video_id = self.youtube_service._extract_video_id(video_url)
            existing_video = await self.get_video_by_youtube_id(video_id)
            
            if existing_video:
                logger.info(f"Video already exists in database: {video_id}")
                return existing_video
            
            # Process the video
            processed_data = await self.process_video_url(video_url)
            
            # Save to database
            saved_video = await self.create_video(processed_data)
            
            return saved_video
            
        except Exception as e:
            logger.error(f"Error processing and saving video: {str(e)}")
            raise