from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings
from typing import Optional


class DatabaseManager:
    client: Optional[AsyncIOMotorClient] = None
    
    def __init__(self):
        self._db = None
        self._collections = {}
    
    async def connect(self):
        """
        Creates database connection and initializes collections.
        This runs when our application starts.
        """
        print("Connecting to MongoDB...")
        self.client = AsyncIOMotorClient(settings.MONGODB_URL)
        self._db = self.client[settings.DATABASE_NAME]
        await self._setup_collections()
        print("Connected to MongoDB!")
    
    async def close(self):
        """
        Closes database connection.
        This runs when our application shuts down.
        """
        if self.client:
            self.client.close()
            print("Closed MongoDB connection.")
    
    async def _setup_collections(self):
        """
        Sets up database collections and their indexes.
        This ensures our database is properly structured.
        """
        # Books collection
        await self._db.books.create_index([("source_video.id", 1)], unique=True)
        await self._db.books.create_index([
            ("title", "text"),
            ("summary", "text"),
            ("key_themes", "text")
        ])
        
        # Processing errors collection
        await self._db.processing_errors.create_index([("video_url", 1)])
        await self._db.processing_errors.create_index([("created_at", -1)])
    
    @property
    def db(self):
        """
        Provides access to the database instance.
        """
        assert self._db is not None, "Database is not initialized"
        return self._db


# Create a global database instance
db = DatabaseManager()