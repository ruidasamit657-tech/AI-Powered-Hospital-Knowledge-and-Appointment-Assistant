from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api.dependencies import get_db, get_current_active_user, get_current_staff_user, get_current_admin_user
from app.db.models.patient import Patient
from app.db.schemas.patient import PatientCreate, PatientUpdate, PatientResponse

router = APIRouter()

@router.get("/", response_model=List[PatientResponse])
async def get_patients(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    _current_user = Depends(get_current_staff_user)
):
    """Get all patients (staff only)"""
    query = db.query(Patient)
    
    if search:
        query = query.filter(
            (Patient.address.ilike(f"%{search}%")) |
            (Patient.phone.ilike(f"%{search}%")) |
            (Patient.blood_group.ilike(f"%{search}%"))
        )
    
    patients = query.offset(skip).limit(limit).all()
    return patients

@router.get("/me", response_model=PatientResponse)
async def get_my_patient_profile(
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's patient profile"""
    user_id = current_user.get("user_id", current_user.get("sub"))
    patient = db.query(Patient).filter(Patient.user_id == int(user_id)).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found"
        )
    return patient

@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    _current_user = Depends(get_current_staff_user)
):
    """Get patient by ID (staff only)"""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    return patient

@router.post("/", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    patient_data: PatientCreate,
    db: Session = Depends(get_db),
    _current_user = Depends(get_current_staff_user)
):
    """Create a new patient (staff only)"""
    # Check if email is unique
    patient = Patient(**patient_data.model_dump(exclude_none=True))
    
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient

@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: int,
    patient_data: PatientUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Update patient information"""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Check if user is authorized (patient themselves or staff/admin)
    current_user_id = int(current_user.get("user_id", current_user.get("sub")))
    if current_user["role"] not in ["admin", "staff"] and patient.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this patient"
        )
    
    update_data = patient_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(patient, field, value)
    
    db.commit()
    db.refresh(patient)
    return patient

@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    _current_user = Depends(get_current_admin_user)
):
    """Delete patient (admin only)"""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    db.delete(patient)
    db.commit()