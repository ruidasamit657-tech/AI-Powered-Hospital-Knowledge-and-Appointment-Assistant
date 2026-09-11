from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.api.dependencies import get_db, get_current_active_user, get_current_admin_user
from app.db.schemas.appointment import AppointmentCreate, AppointmentUpdate, AppointmentResponse
from app.db.models.appointment import Appointment, AppointmentStatus
from app.db.models.patient import Patient
from app.db.models.doctor import Doctor

router = APIRouter()

# FastAPI injects these endpoint dependencies and query parameters.
# pylint: disable=too-many-arguments,too-many-positional-arguments
@router.get(
    "/",
    response_model=List[AppointmentResponse],
)
async def get_appointments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    patient_id: Optional[str] = None,
    doctor_id: Optional[str] = None,
    appointment_status: Optional[str] = Query(None, alias="status"),
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get appointments with filters."""
    query = db.query(Appointment)

    # Role-based filtering
    if current_user["role"] == "patient":
        # Patients can only see their own appointments.
        patient = db.query(Patient).filter(Patient.user_id == current_user["user_id"]).first()
        if patient:
            query = query.filter(Appointment.patient_id == patient.id)
    elif current_user["role"] == "doctor":
        # Doctors can only see their own appointments.
        doctor = db.query(Doctor).filter(Doctor.user_id == current_user["user_id"]).first()
        if doctor:
            query = query.filter(Appointment.doctor_id == doctor.id)

    # Additional filters for staff and administrators.
    if patient_id:
        query = query.filter(Appointment.patient_id == patient_id)
    if doctor_id:
        query = query.filter(Appointment.doctor_id == doctor_id)
    if appointment_status:
        query = query.filter(Appointment.status == appointment_status)
    if date_from:
        query = query.filter(Appointment.appointment_date >= date_from)
    if date_to:
        query = query.filter(Appointment.appointment_date <= date_to)
    
    appointments = (
        query.order_by(Appointment.appointment_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return appointments

@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get appointment by ID"""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    
    # Check authorization
    if current_user["role"] == "patient":
        patient = db.query(Patient).filter(Patient.user_id == current_user["user_id"]).first()
        if patient and appointment.patient_id != patient.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this appointment"
            )
    elif current_user["role"] == "doctor":
        doctor = db.query(Doctor).filter(Doctor.user_id == current_user["user_id"]).first()
        if doctor and appointment.doctor_id != doctor.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this appointment"
            )
    
    return appointment

@router.post("/", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    appointment_data: AppointmentCreate,
    db: Session = Depends(get_db),
    _current_user = Depends(get_current_active_user)
):
    """Create a new appointment"""
    # Check if patient exists
    patient = db.query(Patient).filter(Patient.id == appointment_data.patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Check if doctor exists
    doctor = db.query(Doctor).filter(Doctor.id == appointment_data.doctor_id).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found"
        )
    
    # Check if doctor is available
    if not doctor.is_available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Doctor is not available"
        )
    
    # Check for overlapping appointments
    existing = db.query(Appointment).filter(
        Appointment.doctor_id == appointment_data.doctor_id,
        Appointment.appointment_date == appointment_data.appointment_date,
        Appointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED])
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Doctor already has an appointment at this time"
        )
    
    appointment = Appointment(**appointment_data.model_dump())
    
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment

@router.put("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: str,
    appointment_data: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Update appointment"""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    
    # Check authorization
    if current_user["role"] == "patient":
        patient = db.query(Patient).filter(Patient.user_id == current_user["user_id"]).first()
        if patient and appointment.patient_id != patient.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this appointment"
            )
    
    update_data = appointment_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(appointment, field, value)
    
    db.commit()
    db.refresh(appointment)
    return appointment

@router.put("/{appointment_id}/status", response_model=AppointmentResponse)
async def update_appointment_status(
    appointment_id: str,
    appointment_status: str = Query(..., alias="status"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Update appointment status"""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    
    # Check if status is valid
    if appointment_status not in [s.value for s in AppointmentStatus]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid status"
        )
    
    # Check authorization
    if current_user["role"] == "patient" and appointment_status != AppointmentStatus.CANCELLED.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Patients can only cancel appointments"
        )
    
    appointment.status = appointment_status
    db.commit()
    db.refresh(appointment)
    return appointment

@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_appointment(
    appointment_id: str,
    db: Session = Depends(get_db),
    _current_user = Depends(get_current_admin_user)
):
    """Delete appointment (admin only)"""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    
    db.delete(appointment)
    db.commit()