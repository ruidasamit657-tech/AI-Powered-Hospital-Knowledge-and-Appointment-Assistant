from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.crud.crud.base import CRUDBase
from app.db.models.doctor import Doctor
from app.db.models.department import Department
from app.db.models.user import User
from app.db.schemas.doctor import DoctorCreate, DoctorUpdate

class CRUDDoctor(CRUDBase[Doctor, DoctorCreate, DoctorUpdate]):
    def get_by_email(self, db: Session, *, email: str) -> Optional[Doctor]:
        return db.query(Doctor).join(User, Doctor.user_id == User.id).filter(User.email == email).first()

    def get_by_user_id(self, db: Session, *, user_id: str) -> Optional[Doctor]:
        return db.query(Doctor).filter(Doctor.user_id == user_id).first()

    def get_by_department(self, db: Session, *, department_id: int) -> List[Doctor]:
        return db.query(Doctor).filter(Doctor.department_id == department_id).all()

    def get_available_doctors(self, db: Session) -> List[Doctor]:
        return db.query(Doctor).filter(Doctor.is_active.is_(True)).all()

    def get_doctors_by_specialization(self, db: Session, *, specialization: str) -> List[Doctor]:
        return db.query(Doctor).filter(Doctor.specialization.ilike(f"%{specialization}%")).all()

    def search_doctors(self, db: Session, *, search_term: str) -> List[Doctor]:
        return db.query(Doctor).filter(
            or_(
                Doctor.specialization.ilike(f"%{search_term}%"),
                Doctor.qualification.ilike(f"%{search_term}%")
            )
        ).all()

    def update_availability(self, db: Session, *, doctor_id: int, is_available: bool) -> Optional[Doctor]:
        doctor = self.get(db, object_id=doctor_id)
        if doctor:
            doctor.is_active = is_available
            db.add(doctor)
            db.commit()
            db.refresh(doctor)
        return doctor

    def get_doctors_with_department(self, db: Session) -> List[Dict[str, Any]]:
        results = db.query(Doctor, Department).join(
            Department, Doctor.department_id == Department.id
        ).all()
        
        return [
            {
                "doctor": doctor,
                "department": department
            }
            for doctor, department in results
        ]

    def get_available_on_day(self, db: Session, *, day: str) -> List[Doctor]:
        # Filter doctors available on specific day (case-insensitive)
        doctors = db.query(Doctor).filter(Doctor.is_active.is_(True)).all()
        
        available_doctors = []
        for doctor in doctors:
            availability = doctor.availability or {}
            if isinstance(availability, dict):
                available_days = availability.get("days", availability.keys())
            else:
                available_days = availability
            if any(day.lower() == str(available_day).lower() for available_day in available_days):
                available_doctors.append(doctor)
        
        return available_doctors

doctor_crud = CRUDDoctor(Doctor)