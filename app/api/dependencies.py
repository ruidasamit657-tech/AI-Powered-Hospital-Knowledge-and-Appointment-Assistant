from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import get_current_user
from app.db.session import SessionLocal


security = HTTPBearer()


def get_db() -> Generator:
    """Dependency for getting a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user_dep(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Dependency for getting the current authenticated user."""
    return await get_current_user(credentials)


def get_current_active_user(current_user=Depends(get_current_user_dep)):
    """Dependency for getting the current active user."""
    return current_user


def get_current_admin_user(current_user=Depends(get_current_user_dep)):
    """Dependency for getting the current admin user."""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


def get_current_staff_user(current_user=Depends(get_current_user_dep)):
    """Dependency for getting the current staff user."""
    if current_user.get("role") not in ["admin", "staff"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff privileges required",
        )
    return current_user
