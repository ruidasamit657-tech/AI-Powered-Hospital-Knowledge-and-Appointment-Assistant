from sqlalchemy import Boolean, Column, Integer, String, DateTime, Date, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy import text
from app.db.base import Base

class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    date_of_birth = Column(Date)
    gender = Column(String(10))
    blood_group = Column(String(5))
    address = Column(Text)
    phone = Column(String(20))
    emergency_contact = Column(JSON)
    medical_history = Column(JSON, default=[])
    allergies = Column(JSON, default=[])
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", backref="patient_profile")