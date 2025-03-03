"""
Modal function imports.

This file imports the Modal functions to make them available throughout the application.
"""

import modal
import os
from app.core.config import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Modal
try:
    # Try to initialize Modal with the token
    if settings.MODAL_TOKEN:
        modal.config.token = settings.MODAL_TOKEN
        logger.info("Modal token set successfully")
    else:
        logger.warning("No Modal token found in settings")
        
    # Import the Modal functions
    from app.services.audio_extractor import extract_audio
    from app.services.speech_to_text import transcribe_audio
    from app.services.content_processor import process_transcript
    
    logger.info("Modal functions imported successfully")
    
except Exception as e:
    logger.error(f"Error initializing Modal: {str(e)}")
    
    # Create stub functions for testing or local development
    class DummyFunction:
        def remote(self, *args, **kwargs):
            raise NotImplementedError("Modal functions not available")
    
    # Create dummy functions
    extract_audio = DummyFunction()
    transcribe_audio = DummyFunction()
    process_transcript = DummyFunction()
    
    logger.warning("Using dummy Modal functions")