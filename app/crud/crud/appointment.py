from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import between
from datetime import datetime, date as date_type, time
from app.crud.crud.base import CRUDBase
from app.db.models.appointment import Appointment, AppointmentStatus
from app.db.models.doctor import Doctor
from app.db.models.patient import Patient
from app.db.schemas.appointment import AppointmentCreate, AppointmentUpdate

class CRUDAppointment(CRUDBase[Appointment, AppointmentCreate, AppointmentUpdate]):
    def get_by_patient(self, db: Session, *, patient_id: str) -> List[Appointment]:
        return db.query(Appointment).filter(
            Appointment.patient_id == patient_id
        ).order_by(Appointment.appointment_date.desc()).all()

    def get_by_doctor(self, db: Session, *, doctor_id: str) -> List[Appointment]:
        return db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id
        ).order_by(Appointment.appointment_date.desc()).all()

    def get_by_status(self, db: Session, *, status: AppointmentStatus) -> List[Appointment]:
        return db.query(Appointment).filter(Appointment.status == status).all()

    def get_by_date_range(self, db: Session, *, start_date: datetime, end_date: datetime) -> List[Appointment]:
        return db.query(Appointment).filter(
            between(Appointment.appointment_date, start_date, end_date)
        ).all()

    def get_today_appointments(self, db: Session) -> List[Appointment]:
        today = date_type.today()
        start_of_day = datetime.combine(today, time.min)
        end_of_day = datetime.combine(today, time.max)
        
        return db.query(Appointment).filter(
            between(Appointment.appointment_date, start_of_day, end_of_day)
        ).all()

    def get_upcoming_appointments(self, db: Session, *, limit: int = 10) -> List[Appointment]:
        now = datetime.utcnow()
        return db.query(Appointment).filter(
            Appointment.appointment_date > now,
            Appointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED])
        ).order_by(Appointment.appointment_date.asc()).limit(limit).all()

    def update_status(self, db: Session, *, appointment_id: str, status: AppointmentStatus) -> Optional[Appointment]:
        appointment = self.get(db, object_id=appointment_id)
        if appointment:
            appointment.status = status
            db.add(appointment)
            db.commit()
            db.refresh(appointment)
        return appointment

    def check_availability(self, db: Session, *, doctor_id: str, appointment_time: datetime) -> bool:
        # Check for overlapping appointments
        existing = db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == appointment_time,
            Appointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED])
        ).first()
        
        return existing is None

    def get_appointments_with_details(self, db: Session) -> List[Dict[str, Any]]:
        results = db.query(
            Appointment,
            Patient,
            Doctor
        ).join(Patient, Appointment.patient_id == Patient.id).join(
            Doctor, Appointment.doctor_id == Doctor.id
        ).all()
        
        return [
            {
                "appointment": appointment,
                "patient": patient,
                "doctor": doctor
            }
            for appointment, patient, doctor in results
        ]

    def get_by_date_and_doctor(self, db: Session, *, doctor_id: str, date: date_type) -> List[Appointment]:
        start_of_day = datetime.combine(date, time.min)
        end_of_day = datetime.combine(date, time.max)
        
        return db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            between(Appointment.appointment_date, start_of_day, end_of_day)
        ).all()

appointment_crud = CRUDAppointment(Appointment)