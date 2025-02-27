# VidRead - YouTube Content Library Application

VidRead transforms YouTube videos into readable, organized content in a digital library format.

## Project Overview

VidRead treats videos like "books" in a digital library with:

- Categories and tags for organization
- Channels as "publishers"
- Reading lists for personalized collections
- AI-enhanced content extraction and organization

## Technical Stack

- **Backend**: Python with FastAPI, MongoDB, Modal.com for AI processing
- **Database**: MongoDB with collections for videos, categories, channels
- **Processing**: YouTube API + AI enhancement with GPT-4 via Modal.com

## Project Structure

```
backend/
├── app/                  # Main application folder
│   ├── core/            # Essential services and configurations
│   │   ├── config.py    # Configuration settings
│   │   ├── security.py  # Authentication and security
│   │   └── database.py  # Database connection handling
│   │
│   ├── models/          # Data structures and validation
│   │   ├── video.py     # Video-related models
│   │   ├── user.py      # User-related models
│   │   └── library.py   # Library feature models
│   │
│   ├── services/        # Business logic
│   │   ├── video.py     # Video processing logic
│   │   ├── ai.py        # AI processing services
│   │   └── library.py   # Library management
│   │
│   ├── api/            # API endpoints
│   │   ├── v1/         # Version 1 of API
│   │   └── deps.py     # Shared dependencies
│   │
│   └── main.py        # Application entry point
│
├── tests/             # Test files
└── requirements.txt   # Dependencies
```

## Setup Instructions

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/vidread.git
cd vidread
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
MONGODB_URL=mongodb+srv://your_username:your_password@your_cluster.mongodb.net/
DATABASE_NAME=vidread
SECRET_KEY=your-secret-key-here
YOUTUBE_API_KEY=your-youtube-api-key
MODAL_TOKEN=your-modal-token
```

5. **Run the application**

```bash
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000

API documentation will be available at http://localhost:8000/docs

## API Endpoints

### Videos

- `POST /api/v1/videos/process` - Process a YouTube video URL
- `GET /api/v1/videos` - Get videos with filtering
- `GET /api/v1/videos/{video_id}` - Get a specific video
- `PUT /api/v1/videos/{video_id}` - Update a video
- `DELETE /api/v1/videos/{video_id}` - Delete a video

## Core Features

1. **Video Processing Pipeline**

   - YouTube data extraction
   - Transcript retrieval
   - AI-powered content enhancement
   - Structured storage in MongoDB

2. **Content Organization**

   - Categorization and tagging
   - Chapter creation
   - Glossary and key takeaways extraction

3. **Library Management**
   - Reading lists
   - Featured content
   - Content recommendations

## Modal.com AI Processing

The application uses Modal.com for serverless AI processing:

1. AI analyzes video content to generate:

   - Concise summaries
   - Meaningful chapters
   - Key takeaways
   - Glossary items
   - Appropriate categorization

2. Cost-effective approach:
   - Processing runs on Modal's serverless infrastructure
   - Pay only for compute time used
   - Efficient chunking of content for processing

## Development Guidelines

- Follow PEP 8 style guidelines for Python code
- Use async/await for all database operations
- Document all functions and classes
- Add proper error handling
- Write tests for critical functionality

## License

[MIT License](LICENSE)
