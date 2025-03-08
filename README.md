# YTBook - YouTube to Book Conversion Application

YTBook transforms YouTube videos into structured, readable "books" with chapters, summaries, and additional context.

## Project Overview

YTBook converts video content into a digital library format with:

- Complete speech-to-text transcription using OpenAI's Whisper
- AI-generated chapter organization and summaries
- Glossary terms and key takeaways extraction
- Formatted content with consistent structure
- Search and discovery features

## Technical Stack

- **Backend**: Python with FastAPI, MongoDB, Modal.com for serverless computing
- **Database**: MongoDB with collections for books and processing metadata
- **AI Processing**:
  - Audio extraction with yt-dlp and ffmpeg
  - Transcription with OpenAI's Whisper
  - Content processing with OpenAI's GPT-4

## Project Structure

```
backend/
├── app/                  # Main application folder
│   ├── core/             # Essential services and configurations
│   │   ├── config.py     # Configuration settings
│   │   └── database.py   # Database connection handling
│   │
│   ├── services/         # Business logic
│   │   ├── video.py      # Video processing orchestration
│   │   ├── audio_extractor.py    # Audio extraction via Modal
│   │   ├── speech_to_text.py     # Transcription via Modal
│   │   ├── content_processor.py  # Book generation via Modal
│   │   └── modal_functions.py    # Modal integration
│   │
│   └── main.py           # Application entry point
│
├── deploy/               # Modal deployment scripts
│   ├── audio_extractor.py
│   ├── speech_to_text.py
│   └── content_processor.py
│
└── requirements.txt      # Dependencies
```

## Setup Instructions

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/ytbook.git
cd ytbook
```

2. **Set up virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Configure environment variables**

Create a `.env` file in the project root with the following variables:

```
# MongoDB Connection
MONGODB_URL=mongodb+srv://your_username:your_password@your_cluster.mongodb.net/
DATABASE_NAME=ytbook

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256

# Modal.com for serverless computing
MODAL_TOKEN=your-modal-token-here

# OpenAI for content processing
OPENAI_API_KEY=your-openai-api-key-here
```

5. **Deploy Modal Functions**

```bash
# Set up Modal token
modal token new

# Deploy each function
python -m deploy.audio_extractor
python -m deploy.speech_to_text
python -m deploy.content_processor
```

6. **Run the application**

```bash
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000

API documentation will be available at http://localhost:8000/docs

## API Endpoints

### Processing

- `POST /api/v1/process` - Process a YouTube video URL
- `GET /api/v1/books` - Get processed books with filtering
- `GET /api/v1/books/{book_id}` - Get a specific book

## Core Processing Pipeline

1. **Audio Extraction**

   - Extract high-quality audio from YouTube videos
   - Gather video metadata (title, channel, duration)

2. **Transcription with Whisper**

   - Convert speech to text with high accuracy
   - Handle long videos with automatic chunking
   - Preserve speaker timestamps where possible

3. **Book Creation with GPT-4**

   - Generate comprehensive summary
   - Create logical chapter structure
   - Extract key themes and topics
   - Generate glossary of important terms
   - Identify target audience and difficulty level
   - Suggest further reading

4. **Structured Storage**
   - Save complete book structure in MongoDB
   - Enable full-text search across content
   - Track processing status and metadata

## Modal.com Serverless Processing

The application leverages Modal.com for efficient serverless processing:

1. **Distributed Computing**

   - Audio extraction runs in containers with ffmpeg
   - Transcription with Whisper uses GPU acceleration
   - Content processing with GPT-4 splits work into manageable chunks

2. **Cost-effective Approach**

   - Processing runs on demand with no idle costs
   - Scale automatically based on workload
   - Pay only for compute time used

3. **Robust Processing**
   - Handle videos of any length through chunking
   - Process audio and generate content in parallel
   - Retry mechanisms for transient failures

## Book Structure

Each processed video becomes a "book" with:

- **Title & Author**: From video metadata
- **Summary**: Concise overview of content
- **Chapters**: Logical sections with content, key points, examples, and quotes
- **Glossary**: Important terms and definitions
- **Key Themes**: Main topics covered
- **Target Audience**: Intended knowledge level
- **Further Reading**: Related resources

## Development Guidelines

- Follow PEP 8 style guidelines for Python code
- Use async/await for all database operations
- Document all functions and classes
- Add proper error handling
- Write tests for critical functionality

## License

[MIT License](LICENSE)
