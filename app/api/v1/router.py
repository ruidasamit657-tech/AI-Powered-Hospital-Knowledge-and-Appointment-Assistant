from fastapi import APIRouter
from app.api.v1.endpoints import (
    health, auth, users, departments, doctors, patients, appointments, documents, chat
)

router = APIRouter(prefix="/api/v1")

# Include all endpoint routers with their prefixes
router.include_router(health.router, prefix="/health", tags=["Health"])
router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
router.include_router(users.router, prefix="/users", tags=["Users"])
router.include_router(departments.router, prefix="/departments", tags=["Departments"])
router.include_router(doctors.router, prefix="/doctors", tags=["Doctors"])
router.include_router(patients.router, prefix="/patients", tags=["Patients"])
router.include_router(appointments.router, prefix="/appointments", tags=["Appointments"])
router.include_router(documents.router, prefix="/documents", tags=["Documents"])
router.include_router(chat.router, prefix="/chat", tags=["Chat"])