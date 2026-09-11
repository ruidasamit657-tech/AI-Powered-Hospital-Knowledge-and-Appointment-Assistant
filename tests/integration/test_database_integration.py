"""
Integration tests for database operations
"""
import sys
from pathlib import Path

# Add project root to sys.path so `app.*` imports resolve at runtime.
# This must run before the `app.*` imports below, which is why those
# imports intentionally appear after this bootstrap block.
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# pylint: disable=wrong-import-position
from sqlalchemy.orm import Session

from app.db.models.department import Department
from app.db.models.doctor import Doctor

# Pylint cannot resolve these two modules from this test file's static
# import path even though they exist and work at runtime. Pylance needs
# the `type: ignore[import]` hint for the same reason.
# pylint: disable=import-error,no-name-in-module
from app.crud.user import create_user, get_user_by_username  # type: ignore[import]
from app.schemas.user import UserCreate  # type: ignore[import]
# pylint: enable=import-error,no-name-in-module
# pylint: enable=wrong-import-position


class TestDatabaseIntegration:
    """Test database integration"""

    def test_create_and_retrieve_user(self, db_session: Session):
        """Test creating and retrieving a user from database"""
        user_data = UserCreate(
            email="db_test@example.com",
            username="db_test_user",
            full_name="DB Test User",
            password="Test123!",
            role="patient",
        )
        user = create_user(db_session, user_data)

        retrieved = get_user_by_username(db_session, "db_test_user")
        assert retrieved is not None
        assert retrieved.id == user.id
        assert retrieved.email == "db_test@example.com"
        assert retrieved.full_name == "DB Test User"

    def test_create_department(self, db_session: Session):
        """Test creating a department"""
        department = Department(
            name="Test Department",
            description="Test description",
            location="Test Location",
            phone="555-0000",
            head_of_department="Dr. Test",
        )
        db_session.add(department)
        db_session.commit()

        retrieved = (
            db_session.query(Department)
            .filter(Department.name == "Test Department")
            .first()
        )
        assert retrieved is not None
        assert retrieved.id is not None

    def test_create_doctor_with_relationship(self, db_session: Session):
        """Test creating a doctor linked to a department"""
        department = Department(
            name="Cardiology Test",
            description="Heart-related care",
            location="Building A",
            phone="555-1111",
            head_of_department="Dr. Heart",
        )
        db_session.add(department)
        db_session.commit()
        db_session.refresh(department)

        doctor = Doctor(
            name="Dr. Test",
            specialization="Cardiology",
            department_id=department.id,
            email="dr.test@example.com",
            phone="555-2222",
        )
        db_session.add(doctor)
        db_session.commit()
        db_session.refresh(doctor)

        retrieved_doctor = (
            db_session.query(Doctor)
            .filter(Doctor.email == "dr.test@example.com")
            .first()
        )
        assert retrieved_doctor is not None
        assert retrieved_doctor.department_id == department.id
        assert retrieved_doctor.specialization == "Cardiology"