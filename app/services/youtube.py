from pytube import YouTube
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime
import re
import logging
from typing import Dict, Any, Optional, Tuple, List
from app.core.config import settings
from app.models.video import (
    VideoCreate, Channel, Metadata, Thumbnails, 
    LibraryData, Content, Chapter, DifficultyLevel, ContentType
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("settings.YOUTUBE_API_KEY", settings.YOUTUBE_API_KEY)
class YouTubeService:
    """Service for extracting data from YouTube videos."""
    
    def __init__(self):
        self.api_key = settings.YOUTUBE_API_KEY
        
    def _create_youtube_api_client(self):
        """Create a YouTube API client."""
        if not self.api_key:
            raise ValueError("YouTube API key is not configured")
        return build('youtube', 'v3', developerKey=self.api_key)
    
    def generate_slug(self, title: str) -> str:
        """Generate a URL-friendly slug from a title."""
        # Convert to lowercase and replace spaces with hyphens
        slug = title.lower().strip()
        # Remove special characters
        slug = re.sub(r'[^\w\s-]', '', slug)
        # Replace spaces with hyphens
        slug = re.sub(r'[\s]+', '-', slug)
        return slug
    
    async def get_video_details(self, video_url: str) -> Dict[str, Any]:
        """
        Extract basic information about a YouTube video.
        
        Args:
            video_url: Full YouTube video URL or video ID
            
        Returns:
            Dictionary containing video details
        """
        try:
            # Extract video ID from URL if needed
            video_id = self._extract_video_id(video_url)
            
            # Get detailed information using YouTube API
            youtube = self._create_youtube_api_client()
            video_response = youtube.videos().list(
                part='snippet,contentDetails,statistics',
                id=video_id
            ).execute()
            
            if not video_response['items']:
                raise ValueError(f"Video not found: {video_id}")
            
            video_data = video_response['items'][0]
            snippet = video_data['snippet']
            content_details = video_data['contentDetails']
            
            # Get channel details
            channel_id = snippet['channelId']
            channel_response = youtube.channels().list(
                part='snippet',
                id=channel_id
            ).execute()
            
            channel_data = channel_response['items'][0]['snippet']
            
            # Parse duration from ISO 8601 format
            duration_seconds = self._parse_duration(content_details['duration'])
            
            # Create the channel object
            channel = Channel(
                id=channel_id,
                name=snippet['channelTitle'],
                url=f"https://www.youtube.com/channel/{channel_id}",
                expertise_level=None,  # To be determined by AI
                content_quality=None   # To be determined by AI
            )
            
            # Create thumbnails object
            thumbnails = Thumbnails(
                default=snippet['thumbnails']['default']['url'],
                high=snippet['thumbnails']['high']['url']
            )
            
            # Create metadata
            metadata = Metadata(
                description=snippet['description'],
                duration=duration_seconds,
                published_at=datetime.fromisoformat(snippet['publishedAt'].replace('Z', '+00:00')),
                thumbnails=thumbnails,
                language=snippet.get('defaultLanguage', snippet.get('defaultAudioLanguage')),
                subtitles=[],  # Will be populated later
                prerequisites=[],  # To be determined by AI
                learning_outcomes=[],  # To be determined by AI
                estimated_reading_time=None  # To be calculated after transcript processing
            )
            
            # Create initial library data (categories/tags to be enriched by AI)
            library_data = LibraryData(
                categories=[],
                tags=[],
                difficulty=DifficultyLevel.INTERMEDIATE,  # Default, to be updated by AI
                type="video",
                primary_category=None,  # To be determined by AI
                series=None,  # To be determined by AI
                content_structure=ContentType.TUTORIAL,  # Default, to be updated by AI
                certification_track=None,
                skills_covered=[]  # To be determined by AI
            )
            
            # Create initial content structure (to be enriched by AI)
            content = Content(
                summary="",  # To be generated by AI
                chapters=[],  # To be generated by AI
                transcript=None,  # To be extracted
                glossary=[],  # To be generated by AI
                key_takeaways=[]  # To be generated by AI
            )
            
            # Create the final video object
            video = VideoCreate(
                video_id=video_id,
                title=snippet['title'],
                slug=self.generate_slug(snippet['title']),
                channel=channel,
                metadata=metadata,
                library_data=library_data,
                content=content
            )
            
            return video.dict()
            
        except HttpError as e:
            logger.error(f"YouTube API error: {str(e)}")
            raise ValueError(f"Error fetching video data: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing video: {str(e)}")
            raise
    
    async def get_transcript(self, video_id: str) -> Optional[str]:
        """
        Get the transcript of a YouTube video.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            String containing the transcript text or None if unavailable
        """
        try:
            # Use pytube to get the transcript
            yt = YouTube(f"https://www.youtube.com/watch?v={video_id}")
            
            # Get the first available transcript
            captions = yt.captions
            if not captions or '_' not in captions:
                logger.info(f"No captions available for video {video_id}")
                return None
                
            # Get the English transcript if available, otherwise use the first available one
            caption_track = captions.get('en', next(iter(captions.values())))
            transcript = caption_track.generate_srt_captions()
            
            # Clean up the transcript text
            cleaned_transcript = self._clean_transcript(transcript)
            
            return cleaned_transcript
            
        except Exception as e:
            logger.error(f"Error getting transcript: {str(e)}")
            return None
            
    def _extract_video_id(self, video_url: str) -> str:
        """Extract the video ID from a YouTube URL."""
        # If it's already just an ID (11 characters), return it
        if len(video_url) == 11 and re.match(r'^[A-Za-z0-9_-]{11}$', video_url):
            return video_url
            
        # Try to extract ID from various URL formats
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/|youtube\.com\/watch\?.*v=|youtube\.com\/watch\?.*&v=)([^&\n?#]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, video_url)
            if match:
                return match.group(1)
                
        raise ValueError(f"Could not extract video ID from URL: {video_url}")
        
    def _parse_duration(self, duration_str: str) -> int:
        """
        Parse ISO 8601 duration format to seconds.
        
        Example: 'PT1H2M3S' -> 3723 (1 hour, 2 minutes, 3 seconds)
        """
        hours = 0
        minutes = 0
        seconds = 0
        
        # Extract hours
        hour_match = re.search(r'(\d+)H', duration_str)
        if hour_match:
            hours = int(hour_match.group(1))
            
        # Extract minutes
        minute_match = re.search(r'(\d+)M', duration_str)
        if minute_match:
            minutes = int(minute_match.group(1))
            
        # Extract seconds
        second_match = re.search(r'(\d+)S', duration_str)
        if second_match:
            seconds = int(second_match.group(1))
            
        return hours * 3600 + minutes * 60 + seconds
        
    def _clean_transcript(self, srt_transcript: str) -> str:
        """
        Clean up SRT formatted transcript into plain text.
        
        Args:
            srt_transcript: Transcript text in SRT format
            
        Returns:
            Cleaned plain text transcript
        """
        # Remove timestamp lines and subtitle numbers
        lines = srt_transcript.split('\n')
        clean_lines = []
        skip_line = False
        
        for line in lines:
            # Skip empty lines, timestamp lines, and subtitle numbers
            if not line.strip() or re.match(r'^\d+$', line.strip()) or re.match(r'^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$', line.strip()):
                continue
                
            clean_lines.append(line)
            
        # Join into a single text and clean up any extra spaces
        transcript = ' '.join(clean_lines)
        transcript = re.sub(r'\s+', ' ', transcript).strip()
        
        return transcript