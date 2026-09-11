from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_type: Optional[str]
    file_size: Optional[int]
    file_hash: Optional[str]
    title: Optional[str]
    description: Optional[str]
    document_metadata: Optional[dict]
    is_indexed: bool
    chunk_count: int
    uploaded_by: Optional[int]
    uploaded_at: Optional[datetime]
    indexed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)
