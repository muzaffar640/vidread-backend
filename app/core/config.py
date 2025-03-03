from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    # Project metadata
    PROJECT_NAME: str = "YTBook"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # MongoDB settings
    MONGODB_URL: str
    DATABASE_NAME: str = "ytbook"
    
    # Security settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Modal.ai settings
    MODAL_TOKEN: Optional[str] = None
    
    # OpenAI settings
    OPENAI_API_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Creates a cached instance of settings.
    This prevents reading the .env file multiple times.
    """
    return Settings()


settings = get_settings()