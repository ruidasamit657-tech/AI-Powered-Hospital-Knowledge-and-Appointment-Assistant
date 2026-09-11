from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class PatientCreate(BaseModel):
    user_id: int
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    emergency_contact: Optional[Dict[str, Any]] = None
    medical_history: Optional[List[Any]] = None
    allergies: Optional[List[Any]] = None
    is_active: bool = True


class PatientUpdate(BaseModel):
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    emergency_contact: Optional[Dict[str, Any]] = None
    medical_history: Optional[List[Any]] = None
    allergies: Optional[List[Any]] = None
    is_active: Optional[bool] = None


class PatientResponse(BaseModel):
    id: int
    user_id: int
    date_of_birth: Optional[date]
    gender: Optional[str]
    blood_group: Optional[str]
    address: Optional[str]
    phone: Optional[str]
    emergency_contact: Optional[Dict[str, Any]]
    medical_history: Optional[List[Any]]
    allergies: Optional[List[Any]]
    is_active: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)
