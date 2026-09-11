from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class ChatRequest(BaseModel):
    question: str
    use_groq: bool = True
    include_sources: bool = True

class SourceReference(BaseModel):
    document_id: int
    filename: str
    chunk_index: int
    content: str
    similarity_score: float

class ChatResponse(BaseModel):
    answer: str
    sources: Optional[List[SourceReference]] = None
    mode: str  # "retrieval" or "groq"
    timestamp: datetime

class ChatMessage(BaseModel):
    id: int
    session_id: int
    role: str  # "user" or "assistant"
    content: str
    sources: Optional[List[Dict[str, Any]]]
    created_at: datetime

class ChatSession(BaseModel):
    id: int
    user_id: int
    title: str
    messages: List[ChatMessage]
    created_at: datetime
    updated_at: datetime