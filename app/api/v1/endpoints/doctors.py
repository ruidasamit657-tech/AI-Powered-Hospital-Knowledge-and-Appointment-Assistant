from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api.dependencies import (
    get_db,
    get_current_active_user,
    get_current_admin_user,
    get_current_staff_user,
)
from app.db.models.doctor import Doctor
from app.db.models.department import Department
from app.db.schemas.doctor import DoctorCreate, DoctorUpdate, DoctorResponse

router = APIRouter()

@router.get("/", response_model=List[DoctorResponse])
async def get_doctors(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    department_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    _current_user = Depends(get_current_active_user)
):
    """Get all doctors with filters"""
    query = db.query(Doctor)
    
    if department_id:
        query = query.filter(Doctor.department_id == department_id)
    
    if is_active is not None:
        query = query.filter(Doctor.is_active == is_active)
    
    if search:
        query = query.filter(
            (Doctor.specialization.ilike(f"%{search}%")) |
            (Doctor.qualification.ilike(f"%{search}%"))
        )
    
    doctors = query.offset(skip).limit(limit).all()
    return doctors

@router.get("/by-department/{department_id}", response_model=List[DoctorResponse])
async def get_doctors_by_department(
    department_id: str,
    db: Session = Depends(get_db),
    _current_user = Depends(get_current_active_user)
):
    """Get all doctors in a department"""
    doctors = db.query(Doctor).filter(Doctor.department_id == department_id).all()
    return doctors

@router.get("/{doctor_id}", response_model=DoctorResponse)
async def get_doctor(
    doctor_id: str,
    db: Session = Depends(get_db),
    _current_user = Depends(get_current_active_user)
):
    """Get doctor by ID"""
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found"
        )
    return doctor

@router.post("/", response_model=DoctorResponse, status_code=status.HTTP_201_CREATED)
async def create_doctor(
    doctor_data: DoctorCreate,
    db: Session = Depends(get_db),
    _current_user = Depends(get_current_staff_user)
):
    """Create a new doctor"""
    # Check if department exists
    department = db.query(Department).filter(Department.id == doctor_data.department_id).first()
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    
    # Check if email is unique
    doctor = Doctor(**doctor_data.model_dump(exclude_none=True))
    
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor

@router.put("/{doctor_id}", response_model=DoctorResponse)
async def update_doctor(
    doctor_id: str,
    doctor_data: DoctorUpdate,
    db: Session = Depends(get_db),
    _current_user = Depends(get_current_staff_user)
):
    """Update doctor information"""
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found"
        )
    
    update_data = doctor_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(doctor, field, value)
    
    db.commit()
    db.refresh(doctor)
    return doctor

@router.delete("/{doctor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_doctor(
    doctor_id: str,
    db: Session = Depends(get_db),
    _current_user = Depends(get_current_admin_user)
):
    """Delete doctor (admin only)"""
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found"
        )
    
    db.delete(doctor)
    db.commit()