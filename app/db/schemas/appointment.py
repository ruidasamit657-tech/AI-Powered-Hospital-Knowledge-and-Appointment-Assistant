from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.db.models.appointment import AppointmentStatus


class AppointmentCreate(BaseModel):
    patient_id: int
    doctor_id: int
    department_id: Optional[int] = None
    appointment_date: datetime
    duration_minutes: int = 30
    status: AppointmentStatus = AppointmentStatus.SCHEDULED
    symptoms: Optional[str] = None
    notes: Optional[str] = None


class AppointmentUpdate(BaseModel):
    patient_id: Optional[int] = None
    doctor_id: Optional[int] = None
    department_id: Optional[int] = None
    appointment_date: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    status: Optional[AppointmentStatus] = None
    symptoms: Optional[str] = None
    notes: Optional[str] = None


class AppointmentResponse(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    department_id: Optional[int]
    appointment_date: datetime
    duration_minutes: int
    status: AppointmentStatus
    symptoms: Optional[str]
    notes: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)
