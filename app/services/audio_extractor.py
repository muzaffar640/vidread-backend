import modal
import tempfile
import os
from typing import Dict, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define Modal image with yt-dlp for audio extraction
modal_image = modal.Image.debian_slim().apt_install(
    "ffmpeg"
).pip_install(
    "yt-dlp",
    "pydub"
)

# Define Modal app
app = modal.App("ytbook-audio-extractor")

@app.function(image=modal_image, timeout=600)
def extract_audio(video_url: str, output_format: str = "mp3") -> Dict:
    """
    Extract audio from a YouTube video using yt-dlp.
    
    Args:
        video_url: YouTube video URL
        output_format: Audio format (mp3, m4a, etc.)
        
    Returns:
        Dictionary with metadata and audio file path
    """
    import yt_dlp
    from pydub import AudioSegment
    import json
    
    logger.info(f"Extracting audio from {video_url}")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Configure yt-dlp options
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': output_format,
                'preferredquality': '192',
            }],
            'outtmpl': f'{temp_dir}/%(id)s.%(ext)s',
            'writeinfojson': True,
            'quiet': False,
            'no_warnings': False
        }
        
        try:
            # Download audio
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                result = ydl.extract_info(video_url, download=True)
                video_id = result['id']
                
            # Get the downloaded audio file path
            audio_path = f"{temp_dir}/{video_id}.{output_format}"
            info_path = f"{temp_dir}/{video_id}.info.json"
            
            # Verify audio file exists
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
            # Load the audio to get duration and other properties
            audio = AudioSegment.from_file(audio_path)
            
            # Read the info.json file for metadata
            with open(info_path, 'r') as f:
                info = json.load(f)
            
            # Create metadata object
            metadata = {
                'video_id': video_id,
                'title': info.get('title', ''),
                'channel': info.get('channel', ''),
                'channel_id': info.get('channel_id', ''),
                'upload_date': info.get('upload_date', ''),
                'duration': len(audio) / 1000,  # Duration in seconds
                'description': info.get('description', '')
            }
            
            # Read audio file as bytes
            with open(audio_path, 'rb') as f:
                audio_bytes = f.read()
            
            return {
                'metadata': metadata,
                'audio_bytes': audio_bytes
            }
                
        except Exception as e:
            logger.error(f"Error extracting audio: {str(e)}")
            raise
if __name__ == "__main__":
    # For newer Modal versions
    print("Deploying audio extraction function to Modal...")
    modal.run(extract_audio)
    print("Audio extraction function deployed!")