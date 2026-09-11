from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException, status

from app.db.schemas.chat import ChatRequest, ChatResponse, SourceReference

router = APIRouter()


@router.post("/send", response_model=ChatResponse)
async def send_message(chat_request: ChatRequest) -> ChatResponse:
    """Return a safe response when no knowledge-base provider is configured."""
    if not chat_request.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty",
        )

    sources: List[SourceReference] = []
    return ChatResponse(
        answer=(
            "I do not have enough hospital knowledge to answer that yet. "
            "Please contact the hospital directly for assistance."
        ),
        sources=sources if chat_request.include_sources else None,
        mode="retrieval",
        timestamp=datetime.utcnow(),
    )