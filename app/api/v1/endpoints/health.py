from datetime import datetime, timezone
import os
import psutil
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.core.config import settings

router = APIRouter()

@router.get("/")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "hospital-ai-assistant",
        "version": "1.0.0"
    }

@router.get("/db")
async def db_health_check(db: Session = Depends(get_db)):
    """Database health check endpoint"""
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except SQLAlchemyError as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

@router.get("/system")
async def system_health_check():
    """System health check endpoint with metrics"""
    try:
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "status": "healthy" if cpu_percent < 90 and memory.percent < 90 else "degraded",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "system": {
                "cpu_usage_percent": cpu_percent,
                "memory_usage_percent": memory.percent,
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "disk_usage_percent": disk.percent,
                "disk_free_gb": round(disk.free / (1024**3), 2)
            }
        }
    except (OSError, ValueError) as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e)
        }

@router.get("/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """Readiness check endpoint for Kubernetes/container orchestration"""
    try:
        # Check database
        db.execute(text("SELECT 1"))
        
        # Check vector store
        vector_store_path = settings.VECTOR_STORE_DIR
        os.makedirs(vector_store_path, exist_ok=True)
        
        return {
            "status": "ready",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "components": {
                "database": "ready",
                "vector_store": "ready",
                "api": "ready"
            }
        }
    except (OSError, SQLAlchemyError) as e:
        return {
            "status": "not_ready",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e)
        }
