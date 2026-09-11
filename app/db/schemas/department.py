from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DepartmentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    location: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None

class DepartmentResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    location: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True