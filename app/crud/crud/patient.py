from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_
from sqlalchemy.sql.functions import count
from app.crud.crud.base import CRUDBase
from app.db.models.patient import Patient
from app.db.models.user import User
from app.db.schemas.patient import PatientCreate, PatientUpdate

class CRUDPatient(CRUDBase[Patient, PatientCreate, PatientUpdate]):
    def get_by_email(self, db: Session, *, email: str) -> Optional[Patient]:
        return db.query(Patient).join(User, Patient.user_id == User.id).filter(User.email == email).first()

    def get_by_user_id(self, db: Session, *, user_id: str) -> Optional[Patient]:
        return db.query(Patient).filter(Patient.user_id == user_id).first()

    def search_patients(self, db: Session, *, search_term: str) -> List[Patient]:
        return db.query(Patient).join(User, Patient.user_id == User.id).filter(
            or_(
            User.full_name.ilike(f"%{search_term}%"),
            User.email.ilike(f"%{search_term}%"),
            Patient.phone.ilike(f"%{search_term}%")
            )
        ).all()

    def get_by_blood_group(self, db: Session, *, blood_group: str) -> List[Patient]:
        return db.query(Patient).filter(Patient.blood_group == blood_group).all()

    def get_patients_with_appointments(self, db: Session) -> List[Dict[str, Any]]:
        from app.db.models.appointment import Appointment
        results = db.query(
            Patient,
            count(Appointment.id).label('appointment_count')
        ).outerjoin(
            Appointment, Appointment.patient_id == Patient.id
        ).group_by(Patient.id).all()
        
        return [
            {
                "patient": patient,
                "appointment_count": count
            }
            for patient, count in results
        ]

    def update_medical_history(self, db: Session, *, patient_id: str, medical_history: List) -> Optional[Patient]:
        patient = self.get(db, object_id=patient_id)
        if patient:
            patient.medical_history = medical_history
            db.add(patient)
            db.commit()
            db.refresh(patient)
        return patient

    def update_allergies(self, db: Session, *, patient_id: str, allergies: List) -> Optional[Patient]:
        patient = self.get(db, object_id=patient_id)
        if patient:
            patient.allergies = allergies
            db.add(patient)
            db.commit()
            db.refresh(patient)
        return patient

    def get_patients_by_age_range(self, db: Session, *, min_age: int, max_age: int) -> List[Patient]:
        # Calculate age from date_of_birth
        from datetime import date
        today = date.today()
        
        patients = db.query(Patient).all()
        result = []
        
        for patient in patients:
            if patient.date_of_birth:
                age = today.year - patient.date_of_birth.year - (
                    (today.month, today.day) < (patient.date_of_birth.month, patient.date_of_birth.day)
                )
                if min_age <= age <= max_age:
                    result.append(patient)
        
        return result

patient_crud = CRUDPatient(Patient)