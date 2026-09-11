from sqlalchemy import Column, Integer, DateTime, ForeignKey, Text, Enum, text
from sqlalchemy.orm import relationship
from app.db.base import Base
import enum

class AppointmentStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

class Appointment(Base):
    __tablename__ = "appointments"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    doctor_id = Column(Integer, ForeignKey("doctors.id"))
    department_id = Column(Integer, ForeignKey("departments.id"))
    appointment_date = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=30)
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.SCHEDULED)
    symptoms = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime(timezone=True), onupdate=text("CURRENT_TIMESTAMP"))
    
    # Relationships
    patient = relationship("Patient", backref="appointments")
    doctor = relationship("Doctor", backref="appointments")
    department = relationship("Department", backref="appointments")