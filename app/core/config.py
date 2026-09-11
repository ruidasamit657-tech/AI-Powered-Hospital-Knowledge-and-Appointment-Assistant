from typing import List, Optional
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # App settings
    APP_NAME: str = "Hospital AI Assistant"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ALLOWED_ORIGINS: List[str] = ["http://localhost:8000", "http://127.0.0.1:8000"]
    
    # Database
    DATABASE_URL: str = "sqlite:///./hospital_ai.db"
    
    # JWT
    SECRET_KEY: str = "your-super-secret-key-change-this"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # File upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx", ".txt", ".md"]
    UPLOAD_DIR: str = "data/knowledge_base"
    VECTOR_STORE_DIR: str = "data/vector_index"
    
    # AI/LLM
    OPENAI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"  # Sentence transformers
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    
    # Groq settings
    GROQ_MODEL: str = "mixtral-8x7b-32768"
    
    # Vector store
    VECTOR_STORE_TYPE: str = "chromadb"  # or "faiss"
    
    # Pydantic v2 configuration style
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"  # Prevents crashing if extra variables exist in .env
    )

settings = Settings()

# Create directories safely
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.VECTOR_STORE_DIR, exist_ok=True)
