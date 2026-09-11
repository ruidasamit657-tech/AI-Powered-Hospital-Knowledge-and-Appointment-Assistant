from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict


class DoctorCreate(BaseModel):
    user_id: int
    department_id: Optional[int] = None
    specialization: Optional[str] = None
    qualification: Optional[str] = None
    experience_years: int = 0
    bio: Optional[str] = None
    consultation_fee: Optional[int] = None
    availability: Optional[Dict[str, Any]] = None
    is_active: bool = True


class DoctorUpdate(BaseModel):
    department_id: Optional[int] = None
    specialization: Optional[str] = None
    qualification: Optional[str] = None
    experience_years: Optional[int] = None
    bio: Optional[str] = None
    consultation_fee: Optional[int] = None
    availability: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class DoctorResponse(BaseModel):
    id: int
    user_id: int
    department_id: Optional[int]
    specialization: Optional[str]
    qualification: Optional[str]
    experience_years: int
    bio: Optional[str]
    consultation_fee: Optional[int]
    availability: Optional[Dict[str, Any]]
    is_active: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)
