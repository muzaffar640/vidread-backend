import modal
import tempfile
import os
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define Modal image with whisper for speech recognition
modal_image = modal.Image.debian_slim().apt_install(
    "ffmpeg"
).pip_install(
    "openai",
    "pydub"
)

# Define Modal app
app = modal.App("ytbook-speech-to-text")

@app.function(image=modal_image, timeout=1800, cpu=2.0)
def transcribe_audio(audio_bytes: bytes, metadata: Dict, chunk_size_mb: int = 25) -> Dict:
    """
    Transcribe audio using OpenAI's Whisper model.
    
    Args:
        audio_bytes: Audio file content
        metadata: Video metadata
        chunk_size_mb: Size of audio chunks to process (in MB)
        
    Returns:
        Dictionary with transcription results
    """
    import openai
    from pydub import AudioSegment
    
    logger.info(f"Transcribing audio for video: {metadata['title']}")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Write audio to temp file
        audio_path = f"{temp_dir}/audio.mp3"
        with open(audio_path, 'wb') as f:
            f.write(audio_bytes)
        
        # Load audio file
        audio = AudioSegment.from_file(audio_path)
        duration_ms = len(audio)
        duration_sec = duration_ms / 1000
        
        logger.info(f"Audio duration: {duration_sec} seconds")
        
        # Initialize OpenAI client
        client = openai.OpenAI()
        
        # For short audios (< 10 minutes), transcribe the whole file
        if duration_sec < 600:
            logger.info("Processing audio in a single chunk")
            with open(audio_path, 'rb') as audio_file:
                response = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json"
                )
                
            transcript = response.text
            segments = []
            if hasattr(response, 'segments'):
                segments = response.segments
                
            return {
                'transcript': transcript,
                'segments': segments,
                'duration': duration_sec
            }
        
        # For longer audios, we need to chunk them
        logger.info("Processing long audio in chunks")
        
        # Calculate chunk size in milliseconds
        chunk_size_bytes = chunk_size_mb * 1024 * 1024
        byte_rate = len(audio_bytes) / duration_ms
        chunk_ms = int(chunk_size_bytes / byte_rate)
        
        # Ensure chunk size is reasonable (between 1 and 10 minutes)
        chunk_ms = max(60000, min(chunk_ms, 600000))
        
        logger.info(f"Processing with chunk size: {chunk_ms/1000} seconds")
        
        # Split audio into chunks
        chunks = []
        for i in range(0, len(audio), chunk_ms):
            chunk = audio[i:i + chunk_ms]
            chunk_path = f"{temp_dir}/chunk_{i}.mp3"
            chunk.export(chunk_path, format="mp3")
            chunks.append(chunk_path)
            
        logger.info(f"Split audio into {len(chunks)} chunks")
        
        # Process each chunk
        full_transcript = ""
        all_segments = []
        
        for i, chunk_path in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)}")
            
            try:
                with open(chunk_path, 'rb') as audio_file:
                    response = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="verbose_json"
                    )
                
                # Extract transcript and segments
                chunk_transcript = response.text
                
                # Adjust segment timestamps for this chunk
                chunk_offset = i * chunk_ms / 1000  # Convert to seconds
                chunk_segments = []
                
                if hasattr(response, 'segments'):
                    for segment in response.segments:
                        # Adjust start and end times by the chunk offset
                        segment['start'] += chunk_offset
                        segment['end'] += chunk_offset
                        chunk_segments.append(segment)
                
                # Append to full results
                full_transcript += " " + chunk_transcript
                all_segments.extend(chunk_segments)
                
            except Exception as e:
                logger.error(f"Error processing chunk {i}: {str(e)}")
                full_transcript += " [Error transcribing this section]"
                
        # Return combined results
        return {
            'transcript': full_transcript.strip(),
            'segments': all_segments,
            'duration': duration_sec
        }
if __name__ == "__main__":
    # For newer Modal versions
    print("Deploying speech-to-text function to Modal...")
    modal.run(transcribe_audio)
    print("Speech-to-text function deployed!")