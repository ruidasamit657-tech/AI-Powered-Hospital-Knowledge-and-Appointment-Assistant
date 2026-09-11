from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, text
from app.db.base import Base
import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    STAFF = "staff"
    DOCTOR = "doctor"
    PATIENT = "patient"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.PATIENT)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime(timezone=True), onupdate=text("CURRENT_TIMESTAMP"))