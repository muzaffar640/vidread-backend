import modal
import logging
import json
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.models.video import (
    VideoCreate, Chapter, GlossaryItem, ContentType, 
    DifficultyLevel, ExpertiseLevel
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Modal
modal_app = modal.App("vidread-processing")
modal_image = modal.Image.debian_slim().pip_install(
    "openai", "python-dotenv", "pydantic"
)


@modal_app.cls(image=modal_image)
class ModalProcessor:
    """Modal processor for AI operations."""
    
    @modal.method()
    def process_transcript(self, transcript: str, video_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process video transcript to extract structured content.
        This runs on Modal.com's serverless infrastructure.
        
        Args:
            transcript: Full video transcript text
            video_metadata: Basic video metadata (title, description, etc.)
            
        Returns:
            Dictionary with AI-enhanced content
        """
        import openai
        
        # Configure OpenAI client (on Modal's infrastructure)
        openai_client = openai.OpenAI()
        
        # Helper function to chunk transcript for processing
        def chunk_transcript(text: str, max_chunk_size: int = 4000) -> List[str]:
            words = text.split()
            chunks = []
            current_chunk = []
            current_length = 0
            
            for word in words:
                if current_length + len(word) + 1 > max_chunk_size:
                    chunks.append(" ".join(current_chunk))
                    current_chunk = [word]
                    current_length = len(word)
                else:
                    current_chunk.append(word)
                    current_length += len(word) + 1  # +1 for the space
                    
            if current_chunk:
                chunks.append(" ".join(current_chunk))
                
            return chunks
        
        # 1. Generate Summary
        summary_prompt = f"""
        You are an AI assistant that helps transform YouTube videos into readable content.
        
        Based on the following transcript, create a concise summary (3-5 paragraphs) of the main points.
        
        VIDEO TITLE: {video_metadata['title']}
        VIDEO DESCRIPTION: {video_metadata['description']}
        
        TRANSCRIPT EXCERPT (beginning of video):
        {transcript[:2000] if len(transcript) > 2000 else transcript}
        
        Create a comprehensive summary that captures the main value and content of this video.
        """
        
        summary_response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "You're an AI assistant specializing in content summarization."},
                     {"role": "user", "content": summary_prompt}],
            temperature=0.3,
            max_tokens=600
        )
        
        summary = summary_response.choices[0].message.content
        
        # 2. Identify Key Topics and Categorization
        topic_prompt = f"""
        You are an AI assistant that helps transform YouTube videos into readable content.
        
        Based on the video information and transcript excerpt below, please provide:
        
        1. PRIMARY_CATEGORY: The main category this content belongs to (e.g., Programming, Data Science, Web Development)
        2. CATEGORIES: 3-5 relevant categories this content fits into
        3. TAGS: 5-8 specific tags that accurately represent the video's content
        4. DIFFICULTY: The difficulty level of this content (Beginner, Intermediate, Advanced, or Expert)
        5. CONTENT_STRUCTURE: The type of content this is (Tutorial, Documentation, Case Study, Lecture, Review)
        6. SKILLS_COVERED: List 3-6 specific skills that viewers will learn from this content
        7. PREREQUISITES: List any prerequisite knowledge viewers should have
        8. LEARNING_OUTCOMES: 3-5 things viewers will learn from this content
        
        VIDEO TITLE: {video_metadata['title']}
        VIDEO DESCRIPTION: {video_metadata['description']}
        CHANNEL NAME: {video_metadata['channel_name']}
        
        TRANSCRIPT EXCERPT:
        {transcript[:3000] if len(transcript) > 3000 else transcript}
        
        Respond in the following JSON format:
        {{
            "primary_category": "string",
            "categories": ["string", "string"],
            "tags": ["string", "string"],
            "difficulty": "string",
            "content_structure": "string",
            "skills_covered": ["string", "string"],
            "prerequisites": ["string", "string"],
            "learning_outcomes": ["string", "string"],
            "channel_expertise_level": "string",
            "estimated_reading_time": integer
        }}
        """
        
        topic_response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "You're an AI assistant specializing in content classification."},
                     {"role": "user", "content": topic_prompt}],
            temperature=0.3,
            max_tokens=800,
            response_format={"type": "json_object"}
        )
        
        categorization = json.loads(topic_response.choices[0].message.content)
        
        # For brevity, generate a single chapter
        chapter_prompt = f"""
        You are an AI assistant that helps transform YouTube videos into readable content.
        
        Create meaningful chapters from this transcript.
        Each chapter should have a title, concise content (rewritten for readability), and key points.
        
        VIDEO TITLE: {video_metadata['title']}
        
        TRANSCRIPT:
        {transcript[:5000] if len(transcript) > 5000 else transcript}
        
        Create 1-3 logical chapters. Respond in the following JSON format:
        {{
            "chapters": [
                {{
                    "title": "Chapter Title",
                    "content": "Rewritten content in paragraph form...",
                    "timestamp": "Approximate timestamp (e.g., '5:30')",
                    "key_points": ["Key point 1", "Key point 2"]
                }}
            ]
        }}
        """
        
        chapter_response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "You're an AI assistant specializing in content structure."},
                     {"role": "user", "content": chapter_prompt}],
            temperature=0.4,
            max_tokens=1500,
            response_format={"type": "json_object"}
        )
        
        chapters = json.loads(chapter_response.choices[0].message.content).get("chapters", [])
        
        # Extract Key Takeaways
        takeaway_prompt = f"""
        You are an AI assistant that helps transform YouTube videos into readable content.
        
        Based on the video summary and transcript, identify 5-7 key takeaways that represent 
        the most important points or lessons from this content.
        
        SUMMARY:
        {summary}
        
        TRANSCRIPT EXCERPTS:
        {transcript[:1500]}
        ...
        {transcript[-1500:] if len(transcript) > 1500 else ""}
        
        Respond with a list of key takeaways in the following JSON format:
        {{
            "key_takeaways": ["Takeaway 1", "Takeaway 2", "Takeaway 3"]
        }}
        """
        
        takeaway_response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "You're an AI assistant specializing in extracting key information."},
                     {"role": "user", "content": takeaway_prompt}],
            temperature=0.3,
            max_tokens=500,
            response_format={"type": "json_object"}
        )
        
        takeaways = json.loads(takeaway_response.choices[0].message.content).get("key_takeaways", [])
        
        # Create Glossary Items
        glossary_prompt = f"""
        You are an AI assistant that helps transform YouTube videos into readable content.
        
        Based on the video transcript, identify 3-7 important terms or concepts that might be 
        unfamiliar to readers and would benefit from a definition in a glossary.
        
        VIDEO TITLE: {video_metadata['title']}
        CATEGORIES: {', '.join(categorization.get('categories', []))}
        DIFFICULTY: {categorization.get('difficulty', 'Intermediate')}
        
        TRANSCRIPT EXCERPTS:
        {transcript[:2000]}
        ...
        {transcript[-2000:] if len(transcript) > 2000 else ""}
        
        For each term, provide a definition that's relevant to how it's used in this content.
        
        Respond in the following JSON format:
        {{
            "glossary": [
                {{
                    "term": "Term 1",
                    "definition": "Definition of term 1 as used in this content"
                }}
            ]
        }}
        """
        
        glossary_response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "You're an AI assistant specializing in educational content."},
                     {"role": "user", "content": glossary_prompt}],
            temperature=0.4,
            max_tokens=800,
            response_format={"type": "json_object"}
        )
        
        glossary = json.loads(glossary_response.choices[0].message.content).get("glossary", [])
        
        # Combine all processed data
        processed_content = {
            "summary": summary,
            "primary_category": categorization.get("primary_category"),
            "categories": categorization.get("categories", []),
            "tags": categorization.get("tags", []),
            "difficulty": categorization.get("difficulty", "Intermediate"),
            "content_structure": categorization.get("content_structure", "Tutorial"),
            "skills_covered": categorization.get("skills_covered", []),
            "prerequisites": categorization.get("prerequisites", []),
            "learning_outcomes": categorization.get("learning_outcomes", []),
            "channel_expertise_level": categorization.get("channel_expertise_level", "Advanced"),
            "estimated_reading_time": categorization.get("estimated_reading_time", 10),
            "chapters": chapters,
            "key_takeaways": takeaways,
            "glossary": glossary
        }
        
        return processed_content


class AIProcessingService:
    """Service for AI processing of video content using Modal.com."""
    
    def __init__(self):
        self.modal_token = settings.MODAL_TOKEN
        self.use_modal = self.modal_token is not None and self.modal_token != ""
        
        # Initialize Modal client if token is available
        if self.use_modal:
            try:
                modal.set_token(self.modal_token)
                logger.info("Modal token set successfully")
            except Exception as e:
                logger.error(f"Error setting Modal token: {str(e)}")
                self.use_modal = False
    
    async def process_video_content(self, video_data: Dict[str, Any], transcript: Optional[str] = None) -> Dict[str, Any]:
        """
        Process video content using AI to enhance its structure and metadata.
        
        Args:
            video_data: Basic video metadata from YouTube
            transcript: Video transcript text
            
        Returns:
            Enhanced video data with AI-generated content
        """
        if not transcript:
            logger.warning(f"No transcript provided for video {video_data['video_id']}, AI processing will be limited")
            return video_data
            
        try:
            # Create metadata dictionary for Modal function
            video_metadata = {
                "title": video_data["title"],
                "description": video_data["metadata"]["description"],
                "channel_name": video_data["channel"]["name"],
                "duration": video_data["metadata"]["duration"]
            }
            
            # If Modal is available, process with it
            if self.use_modal:
                logger.info("Processing with Modal...")
                try:
                    # Initialize the Modal processor
                    processor = ModalProcessor()
                    
                    # Process content with Modal
                    processed_data = processor.process_transcript.remote(transcript, video_metadata)
                    
                    logger.info("Modal processing completed successfully")
                except Exception as e:
                    logger.error(f"Error in Modal processing: {str(e)}")
                    logger.info("Falling back to simplified processing")
                    processed_data = self._simplified_processing(transcript, video_metadata)
            else:
                logger.info("Modal not available, using simplified processing")
                processed_data = self._simplified_processing(transcript, video_metadata)
            
            # Update video data with processed content
            
            # Update content fields
            video_data["content"]["summary"] = processed_data["summary"]
            
            # Process chapters
            chapters = []
            for chapter_data in processed_data.get("chapters", []):
                chapters.append({
                    "title": chapter_data["title"],
                    "content": chapter_data["content"],
                    "timestamp": chapter_data["timestamp"],
                    "key_points": chapter_data["key_points"],
                    "exercises": [],  # No exercises generated yet
                    "resources": []   # No resources generated yet
                })
            video_data["content"]["chapters"] = chapters
            
            # Add transcript
            video_data["content"]["transcript"] = transcript
            
            # Process glossary
            glossary = []
            for glossary_item in processed_data.get("glossary", []):
                glossary.append({
                    "term": glossary_item["term"],
                    "definition": glossary_item["definition"]
                })
            video_data["content"]["glossary"] = glossary
            
            # Add key takeaways
            video_data["content"]["key_takeaways"] = processed_data.get("key_takeaways", [])
            
            # Update metadata
            video_data["metadata"]["prerequisites"] = processed_data.get("prerequisites", [])
            video_data["metadata"]["learning_outcomes"] = processed_data.get("learning_outcomes", [])
            video_data["metadata"]["estimated_reading_time"] = processed_data.get("estimated_reading_time", 5)
            
            # Update library data
            video_data["library_data"]["categories"] = processed_data.get("categories", [])
            video_data["library_data"]["tags"] = processed_data.get("tags", [])
            video_data["library_data"]["primary_category"] = processed_data.get("primary_category")
            video_data["library_data"]["content_structure"] = processed_data.get("content_structure", "Tutorial")
            video_data["library_data"]["skills_covered"] = processed_data.get("skills_covered", [])
            
            # Map the difficulty string to enum
            difficulty_map = {
                "Beginner": DifficultyLevel.BEGINNER,
                "Intermediate": DifficultyLevel.INTERMEDIATE,
                "Advanced": DifficultyLevel.ADVANCED,
                "Expert": DifficultyLevel.EXPERT
            }
            video_data["library_data"]["difficulty"] = difficulty_map.get(
                processed_data.get("difficulty", "Intermediate"), 
                DifficultyLevel.INTERMEDIATE
            )
            
            # Update channel expertise level
            expertise_map = {
                "Beginner-Friendly": ExpertiseLevel.BEGINNER_FRIENDLY,
                "Advanced": ExpertiseLevel.ADVANCED,
                "Expert": ExpertiseLevel.EXPERT
            }
            video_data["channel"]["expertise_level"] = expertise_map.get(
                processed_data.get("channel_expertise_level", "Advanced"),
                ExpertiseLevel.ADVANCED
            )
            
            # Set a reasonable content quality score (1-10)
            quality_map = {
                ExpertiseLevel.BEGINNER_FRIENDLY: 7,
                ExpertiseLevel.ADVANCED: 8,
                ExpertiseLevel.EXPERT: 9
            }
            video_data["channel"]["content_quality"] = quality_map.get(
                video_data["channel"]["expertise_level"],
                8
            )
            
            return video_data
            
        except Exception as e:
            logger.error(f"Error in AI processing: {str(e)}")
            logger.exception(e)
            # Return original data if processing fails
            return video_data
    
    def _simplified_processing(self, transcript: str, video_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simplified processing for when Modal is not available.
        
        Args:
            transcript: Video transcript text
            video_metadata: Basic video metadata
            
        Returns:
            Dictionary with basic processed content
        """
        # Create a simple summary (first 500 chars of transcript)
        summary = transcript[:500]
        if len(transcript) > 500:
            summary += "..."
        
        # Create basic chapter structure
        chapter_length = min(len(transcript), 1000)
        chapter_content = transcript[:chapter_length]
        if len(transcript) > chapter_length:
            chapter_content += "..."
            
        chapters = [
            {
                "title": "Introduction",
                "content": chapter_content,
                "timestamp": "0:00",
                "key_points": ["Introduction to the content"]
            }
        ]
        
        # If transcript is long enough, add more chapters
        if len(transcript) > 1000:
            mid_point = min(len(transcript) // 2, 3000)
            mid_content = transcript[mid_point:mid_point+1000]
            if len(transcript) > mid_point+1000:
                mid_content += "..."
                
            chapters.append({
                "title": "Main Content",
                "content": mid_content,
                "timestamp": "5:00",
                "key_points": ["Main discussion points"]
            })
        
        if len(transcript) > 4000:
            end_point = max(0, len(transcript) - 1000)
            end_content = transcript[end_point:]
            
            chapters.append({
                "title": "Conclusion",
                "content": end_content,
                "timestamp": "10:00",
                "key_points": ["Summary and conclusions"]
            })
        
        # Create basic glossary with placeholders
        glossary = [
            {"term": "Topic 1", "definition": "Definition for Topic 1"},
            {"term": "Topic 2", "definition": "Definition for Topic 2"}
        ]
        
        # Create key takeaways
        key_takeaways = [
            "Key point from the video",
            "Another important concept covered"
        ]
        
        return {
            "summary": summary,
            "primary_category": "Education",
            "categories": ["Education", "Technology"],
            "tags": ["learning", "tutorial"],
            "difficulty": "Intermediate",
            "content_structure": "Tutorial",
            "skills_covered": ["Technical knowledge", "Understanding concepts"],
            "prerequisites": ["Basic understanding of the subject"],
            "learning_outcomes": ["Understanding of key concepts"],
            "channel_expertise_level": "Advanced",
            "estimated_reading_time": len(transcript) // 1000,  # ~1 min per 1000 chars
            "chapters": chapters,
            "key_takeaways": key_takeaways,
            "glossary": glossary
        }