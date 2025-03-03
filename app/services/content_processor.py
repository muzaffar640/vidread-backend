import modal
import json
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define Modal image with OpenAI for content processing
modal_image = modal.Image.debian_slim().pip_install(
    "openai",
    "tiktoken"
)

# Define Modal app
app = modal.App("ytbook-content-processor")

@app.function(image=modal_image)
def process_transcript(transcript: str, metadata: Dict, max_tokens_per_chunk: int = 12000) -> Dict:
    """
    Process transcript into a structured book format using OpenAI's GPT-4.
    
    Args:
        transcript: Full transcript text
        metadata: Video metadata
        max_tokens_per_chunk: Maximum tokens to process in each chunk
        
    Returns:
        Dictionary with structured book content
    """
    import openai
    import tiktoken
    
    logger.info(f"Processing transcript for video: {metadata['title']}")
    
    # Initialize OpenAI client
    client = openai.OpenAI()
    
    # Function to count tokens
    def count_tokens(text: str) -> int:
        encoding = tiktoken.encoding_for_model("gpt-4")
        return len(encoding.encode(text))
    
    # Function to chunk text by tokens
    def chunk_by_tokens(text: str, max_tokens: int) -> List[str]:
        if count_tokens(text) <= max_tokens:
            return [text]
            
        words = text.split()
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for word in words:
            word_tokens = count_tokens(word + " ")
            if current_tokens + word_tokens > max_tokens:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_tokens = word_tokens
            else:
                current_chunk.append(word)
                current_tokens += word_tokens
                
        if current_chunk:
            chunks.append(" ".join(current_chunk))
            
        return chunks
    
    # 1. First stage: Create a concise summary and chapter outline
    overview_prompt = f"""
    You are a professional editor converting a video transcript into an organized, readable book format.
    
    VIDEO INFORMATION:
    Title: {metadata['title']}
    Channel: {metadata['channel']}
    Duration: {metadata['duration']} seconds
    
    Based on this transcript, create:
    1. A concise summary of the content (3-5 paragraphs)
    2. An outline with 5-10 chapter titles that logically organize the content
    3. Key themes and topics covered
    4. Target audience and knowledge level
    
    TRANSCRIPT EXCERPT (beginning):
    {transcript[:3000] if len(transcript) > 3000 else transcript}
    
    TRANSCRIPT EXCERPT (middle):
    {transcript[len(transcript)//2-1500:len(transcript)//2+1500] if len(transcript) > 3000 else ""}
    
    TRANSCRIPT EXCERPT (end):
    {transcript[-3000:] if len(transcript) > 3000 else ""}
    
    Return your response in JSON format with these fields:
    {{"summary": "...", "chapter_outline": ["Chapter 1: ...", ...], "key_themes": ["...", ...], "target_audience": "...", "difficulty_level": "..."}}
    """
    
    try:
        overview_response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional editor converting video content into book format."},
                {"role": "user", "content": overview_prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        overview_data = json.loads(overview_response.choices[0].message.content)
        logger.info("Generated summary and chapter outline")
        
        # 2. Second stage: Process transcript into chapters
        chapter_outline = overview_data.get("chapter_outline", [])
        chapters = []
        
        # Chunk the transcript to process with context
        transcript_chunks = chunk_by_tokens(transcript, max_tokens_per_chunk)
        logger.info(f"Split transcript into {len(transcript_chunks)} chunks for processing")
        
        for i, chunk in enumerate(transcript_chunks):
            # Calculate progress through transcript
            progress = (i + 1) / len(transcript_chunks)
            
            # Determine which chapters to focus on based on position in transcript
            if len(chapter_outline) <= 3:
                # For few chapters, process all at once
                chapters_to_process = chapter_outline
            else:
                # For more chapters, estimate which ones are relevant to this chunk
                start_idx = int(progress * len(chapter_outline) * 0.8)  # Adjust start index
                start_idx = max(0, min(start_idx, len(chapter_outline) - 1))
                
                end_idx = int(progress * len(chapter_outline) * 1.2) + 1  # Adjust end index
                end_idx = max(start_idx + 1, min(end_idx, len(chapter_outline)))
                
                # For first and last chunk, include more context
                if i == 0:
                    end_idx = min(3, len(chapter_outline))
                    chapters_to_process = chapter_outline[:end_idx]
                elif i == len(transcript_chunks) - 1:
                    start_idx = max(len(chapter_outline) - 3, 0)
                    chapters_to_process = chapter_outline[start_idx:]
                else:
                    chapters_to_process = chapter_outline[start_idx:end_idx]
            
            chapter_prompt = f"""
            You are converting a video transcript into a structured book format.
            
            VIDEO INFORMATION:
            Title: {metadata['title']}
            
            You need to create the following chapters based on this transcript chunk:
            {json.dumps(chapters_to_process)}
            
            This is chunk {i+1} of {len(transcript_chunks)} from the transcript.
            
            TRANSCRIPT CHUNK:
            {chunk}
            
            For each chapter in the list, if the transcript chunk contains relevant content:
            1. Create a well-written, clear, and concise section of text
            2. Include 3-5 key points that summarize the most important information
            3. Add any relevant examples or case studies mentioned
            4. Note any important quotes or statistics
            
            Format your response as a JSON object with chapters as keys and content objects as values:
            {{
              "Chapter Title": {{
                "content": "Rewritten content in clear paragraphs...",
                "key_points": ["Key point 1", "Key point 2", ...],
                "examples": ["Example 1", ...],
                "quotes": ["Quote 1", ...]
              }},
              ...
            }}
            
            Only include chapters that can be created from this specific transcript chunk. Skip chapters if there's no relevant content in this chunk.
            """
            
            try:
                chapter_response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a professional editor converting video content into book format."},
                        {"role": "user", "content": chapter_prompt}
                    ],
                    temperature=0.3,
                    response_format={"type": "json_object"}
                )
                
                chunk_chapters = json.loads(chapter_response.choices[0].message.content)
                
                # Merge with existing chapters
                for title, content in chunk_chapters.items():
                    chapter_exists = False
                    
                    for chapter in chapters:
                        if chapter["title"] == title:
                            # Append to existing chapter content
                            chapter["content"] += "\n\n" + content["content"]
                            chapter["key_points"].extend(content.get("key_points", []))
                            chapter["examples"].extend(content.get("examples", []))
                            chapter["quotes"].extend(content.get("quotes", []))
                            chapter_exists = True
                            break
                            
                    if not chapter_exists:
                        # Create new chapter
                        chapters.append({
                            "title": title,
                            "content": content["content"],
                            "key_points": content.get("key_points", []),
                            "examples": content.get("examples", []),
                            "quotes": content.get("quotes", [])
                        })
                
                logger.info(f"Processed chunk {i+1}/{len(transcript_chunks)}")
                
            except Exception as e:
                logger.error(f"Error processing chunk {i+1}: {str(e)}")
        
        # 3. Third stage: Create glossary and additional book elements
        glossary_prompt = f"""
        You are creating a glossary for a book based on this video transcript.
        
        VIDEO INFORMATION:
        Title: {metadata['title']}
        Summary: {overview_data.get('summary', '')}
        Key Themes: {json.dumps(overview_data.get('key_themes', []))}
        
        Based on the summary and key themes, identify 5-15 important terms, concepts, or jargon that would benefit from definition in a glossary.
        
        For each term, provide a clear, concise definition as it relates to the content of this video.
        
        Return your response as a JSON object with terms as keys and definitions as values:
        {{
          "Term 1": "Definition 1",
          "Term 2": "Definition 2",
          ...
        }}
        """
        
        try:
            glossary_response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a professional editor creating a glossary."},
                    {"role": "user", "content": glossary_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            glossary = json.loads(glossary_response.choices[0].message.content)
            logger.info(f"Created glossary with {len(glossary)} terms")
            
        except Exception as e:
            logger.error(f"Error creating glossary: {str(e)}")
            glossary = {}
        
        # 4. Generate recommendations and further reading
        references_prompt = f"""
        You are a knowledge expert creating a 'Further Reading' section for a book based on this video.
        
        VIDEO INFORMATION:
        Title: {metadata['title']}
        Channel: {metadata['channel']}
        Summary: {overview_data.get('summary', '')}
        Key Themes: {json.dumps(overview_data.get('key_themes', []))}
        
        Generate 5-10 suggestions for further reading or learning related to the content of this video.
        These can include books, articles, courses, or other resources that would be valuable for someone interested in this topic.
        
        For each suggestion, provide a title, author/source, and a brief description of why it's relevant.
        
        Return your response as a JSON array:
        [
          {{
            "title": "Resource Title",
            "author": "Author/Source",
            "description": "Brief description of relevance"
          }},
          ...
        ]
        """
        
        try:
            references_response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a knowledge expert creating recommendations for further reading."},
                    {"role": "user", "content": references_prompt}
                ],
                temperature=0.4,
                response_format={"type": "json_object"}
            )
            
            further_reading = json.loads(references_response.choices[0].message.content)
            logger.info(f"Generated {len(further_reading)} further reading suggestions")
            
        except Exception as e:
            logger.error(f"Error generating further reading: {str(e)}")
            further_reading = []
        
        # 5. Create final book structure
        processed_content = {
            "title": metadata['title'],
            "author": metadata['channel'],
            "summary": overview_data.get('summary', ''),
            "chapters": chapters,
            "glossary": glossary,
            "further_reading": further_reading,
            "key_themes": overview_data.get('key_themes', []),
            "target_audience": overview_data.get('target_audience', ''),
            "difficulty_level": overview_data.get('difficulty_level', ''),
            "source_video": {
                "id": metadata['video_id'],
                "url": f"https://www.youtube.com/watch?v={metadata['video_id']}",
                "duration": metadata['duration'],
                "upload_date": metadata.get('upload_date', '')
            }
        }
        
        logger.info("Content processing completed successfully")
        return processed_content
        
    except Exception as e:
        logger.error(f"Error in content processing: {str(e)}")
        raise