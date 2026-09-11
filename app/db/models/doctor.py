from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, JSON, text
from sqlalchemy.orm import relationship
from app.db.base import Base

class Doctor(Base):
    __tablename__ = "doctors"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    department_id = Column(Integer, ForeignKey("departments.id"))
    specialization = Column(String(100))
    qualification = Column(Text)
    experience_years = Column(Integer, default=0)
    bio = Column(Text)
    consultation_fee = Column(Integer)
    availability = Column(JSON, default=[])  # Store availability schedule
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime(timezone=True), onupdate=text("CURRENT_TIMESTAMP"))
    
    # Relationships
    user = relationship("User", backref="doctor_profile")
    department = relationship("Department", backref="doctors")