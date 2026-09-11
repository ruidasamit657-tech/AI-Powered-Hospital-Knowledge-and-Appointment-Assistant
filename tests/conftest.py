# pyright: reportMissingImports=false
# pylint: disable=wrong-import-position, no-name-in-module, import-error

"""
Pytest configuration and shared fixtures
"""

# 1. Standard library and third-party imports at the absolute top
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# 2. Modify sys.path AFTER third-party imports but BEFORE local app imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 3. Local application imports
# Each line carries `# type: ignore` because Pylance evaluates the file
# statically, before `sys.path.insert` runs. This is the only in-file way
# to reliably silence `reportMissingImports` on these specific lines.
from app.core.security import security  # type: ignore[import]
from app.crud.user import create_user  # type: ignore[import]
from app.db.base import Base  # type: ignore[import]
from app.db.models.user import UserRole  # type: ignore[import]
from app.db.session import get_db  # type: ignore[import]
from app.main import app  # type: ignore[import]
from app.schemas.user import UserCreate  # type: ignore[import]


# Test database URL (in-memory SQLite for tests)
TEST_DATABASE_URL = "sqlite:///./test.db"

# Create test engine
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Override get_db dependency
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


# Test client fixture
@pytest.fixture
def client():
    """Create test client"""
    # Create tables
    Base.metadata.create_all(bind=engine)

    with TestClient(app) as test_client:
        yield test_client

    # Clean up after tests
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """Get test database session"""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


# Disable redefinition warnings globally for the dependent test fixtures below
# pylint: disable=redefined-outer-name


@pytest.fixture
def test_user(db_session):
    """Create a test user"""
    user_data = UserCreate(
        email="testuser@example.com",
        username="testuser",
        full_name="Test User",
        password="Test123!",
        role=UserRole.PATIENT,
    )
    user = create_user(db_session, user_data)
    return user


@pytest.fixture
def test_admin_user(db_session):
    """Create a test admin user"""
    admin_data = UserCreate(
        email="admin@example.com",
        username="admin",
        full_name="Admin User",
        password="Admin123!",
        role=UserRole.ADMIN,
    )
    user = create_user(db_session, admin_data)
    return user


@pytest.fixture
def test_token(test_user):
    """Create a test JWT token"""
    token = security.create_access_token(
        data={"sub": test_user.username, "role": test_user.role}
    )
    return token


@pytest.fixture
def admin_token(test_admin_user):
    """Create an admin JWT token"""
    token = security.create_access_token(
        data={"sub": test_admin_user.username, "role": test_admin_user.role}
    )
    return token


@pytest.fixture
def auth_headers(test_token):
    """Get authentication headers for testing"""
    return {"Authorization": f"Bearer {test_token}"}


@pytest.fixture
def admin_headers(admin_token):
    """Get admin authentication headers for testing"""
    return {"Authorization": f"Bearer {admin_token}"}


# pylint: enable=redefined-outer-name


@pytest.fixture
def sample_department_data():
    """Sample department data for testing"""
    return {
        "name": "Test Cardiology",
        "description": "Test department for testing",
        "location": "Floor 3, Building A",
        "phone": "555-0200",
        "head_of_department": "Dr. Test",
    }


@pytest.fixture
def sample_doctor_data():
    """Sample doctor data for testing"""
    return {
        "first_name": "Test",
        "last_name": "Doctor",
        "email": "test.doctor@hospital.com",
        "phone": "555-0301",
        "specialization": "Cardiologist",
        "qualifications": ["MD", "FACC"],
        "experience_years": 10,
        "department_id": 1,
        "available_days": ["Monday", "Wednesday", "Friday"],
        "available_hours": ["09:00-12:00", "14:00-17:00"],
        "is_active": "active",
        "bio": "Test doctor for testing",
    }


@pytest.fixture
def sample_patient_data():
    """Sample patient data for testing"""
    return {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@email.com",
        "phone": "555-0401",
        "date_of_birth": "1980-05-15",
        "gender": "Male",
        "blood_type": "O+",
        "allergies": ["Penicillin"],
        "medical_history": {
            "conditions": ["Hypertension"],
            "medications": ["Lisinopril"],
        },
        "emergency_contact": {
            "name": "Jane Doe",
            "relationship": "Spouse",
            "phone": "555-0402",
        },
        "address": {
            "street": "123 Main St",
            "city": "Springfield",
            "state": "IL",
            "zip": "62701",
        },
    }


@pytest.fixture
def sample_appointment_data():
    """Sample appointment data for testing"""
    return {
        "patient_id": 1,
        "doctor_id": 1,
        "appointment_date": "2026-09-30T10:00:00",
        "appointment_time": "10:00 AM",
        "status": "scheduled",
        "reason": "Annual checkup",
        "notes": "Test appointment",
    }


@pytest.fixture
def sample_chat_request():
    """Sample chat request for testing"""
    return {
        "question": "What are the hospital visiting hours?",
        "use_groq": False,
        "include_sources": True,
    }


@pytest.fixture
def sample_emergency_chat_request():
    """Sample emergency chat request for testing"""
    return {
        "question": "I think I'm having a heart attack!",
        "use_groq": False,
        "include_sources": True,
    }