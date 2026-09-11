
"""
Unit tests for appointment endpoints
"""

import pytest
from fastapi.testclient import TestClient


class TestAppointments:
    """Test appointment CRUD operations"""

    @pytest.fixture
    def setup_patient_and_doctor(self, client: TestClient, admin_headers, 
                                  sample_patient_data, sample_doctor_data, 
                                  sample_department_data):
        """Setup a patient and doctor for appointment tests"""
        # Create department
        dept_response = client.post(
            "/api/v1/departments",
            headers=admin_headers,
            json=sample_department_data
        )
        department_id = dept_response.json()["id"]
        
        # Create doctor
        sample_doctor_data["department_id"] = department_id
        doctor_response = client.post(
            "/api/v1/doctors",
            headers=admin_headers,
            json=sample_doctor_data
        )
        doctor_id = doctor_response.json()["id"]
        
        # Create patient
        patient_response = client.post(
            "/api/v1/patients",
            headers=admin_headers,
            json=sample_patient_data
        )
        patient_id = patient_response.json()["id"]
        
        return {
            "department_id": department_id,
            "doctor_id": doctor_id,
            "patient_id": patient_id
        }

    # ==========================================
    # CREATE APPOINTMENT TESTS
    # ==========================================

    def test_create_appointment(self, client: TestClient, admin_headers, 
                                 setup_patient_and_doctor):
        """Test creating an appointment"""
        ids = setup_patient_and_doctor
        
        appointment_data = {
            "patient_id": ids["patient_id"],
            "doctor_id": ids["doctor_id"],
            "appointment_date": "2026-10-15T10:00:00",
            "appointment_time": "10:00 AM",
            "status": "scheduled",
            "reason": "Annual checkup",
            "notes": "Patient requested morning appointment"
        }
        
        response = client.post(
            "/api/v1/appointments",
            headers=admin_headers,
            json=appointment_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["patient_id"] == ids["patient_id"]
        assert data["doctor_id"] == ids["doctor_id"]
        assert data["appointment_time"] == "10:00 AM"
        assert data["status"] == "scheduled"
        assert data["reason"] == "Annual checkup"
        assert "id" in data
        assert "created_at" in data

    def test_create_appointment_invalid_patient(self, client: TestClient, 
                                                  admin_headers, 
                                                  setup_patient_and_doctor):
        """Test creating appointment with invalid patient ID"""
        ids = setup_patient_and_doctor
        
        appointment_data = {
            "patient_id": 99999,  # Invalid
            "doctor_id": ids["doctor_id"],
            "appointment_date": "2026-10-15T10:00:00",
            "appointment_time": "10:00 AM",
            "status": "scheduled",
            "reason": "Test"
        }
        
        response = client.post(
            "/api/v1/appointments",
            headers=admin_headers,
            json=appointment_data
        )
        
        assert response.status_code == 404
        assert "Patient not found" in response.text

    def test_create_appointment_invalid_doctor(self, client: TestClient, 
                                                 admin_headers, 
                                                 setup_patient_and_doctor):
        """Test creating appointment with invalid doctor ID"""
        ids = setup_patient_and_doctor
        
        appointment_data = {
            "patient_id": ids["patient_id"],
            "doctor_id": 99999,  # Invalid
            "appointment_date": "2026-10-15T10:00:00",
            "appointment_time": "10:00 AM",
            "status": "scheduled",
            "reason": "Test"
        }
        
        response = client.post(
            "/api/v1/appointments",
            headers=admin_headers,
            json=appointment_data
        )
        
        assert response.status_code == 404
        assert "Doctor not found" in response.text

    def test_create_appointment_missing_fields(self, client: TestClient, 
                                                 admin_headers):
        """Test creating appointment with missing required fields"""
        appointment_data = {
            "patient_id": 1
            # Missing doctor_id, appointment_date, appointment_time
        }
        
        response = client.post(
            "/api/v1/appointments",
            headers=admin_headers,
            json=appointment_data
        )
        
        assert response.status_code == 422  # Validation error

    # ==========================================
    # GET APPOINTMENTS TESTS
    # ==========================================

    def test_get_all_appointments(self, client: TestClient, auth_headers):
        """Test getting all appointments"""
        response = client.get(
            "/api/v1/appointments",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_specific_appointment(self, client: TestClient, admin_headers,
                                       setup_patient_and_doctor):
        """Test getting a specific appointment"""
        ids = setup_patient_and_doctor
        
        # Create appointment
        appointment_data = {
            "patient_id": ids["patient_id"],
            "doctor_id": ids["doctor_id"],
            "appointment_date": "2026-10-15T10:00:00",
            "appointment_time": "10:00 AM",
            "status": "scheduled",
            "reason": "Test"
        }
        create_response = client.post(
            "/api/v1/appointments",
            headers=admin_headers,
            json=appointment_data
        )
        appointment_id = create_response.json()["id"]
        
        # Get appointment
        response = client.get(
            f"/api/v1/appointments/{appointment_id}",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == appointment_id

    def test_get_nonexistent_appointment(self, client: TestClient, auth_headers):
        """Test getting non-existent appointment"""
        response = client.get(
            "/api/v1/appointments/99999",
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_get_appointments_by_patient(self, client: TestClient, admin_headers,
                                          setup_patient_and_doctor):
        """Test filtering appointments by patient"""
        ids = setup_patient_and_doctor
        
        # Create appointment
        appointment_data = {
            "patient_id": ids["patient_id"],
            "doctor_id": ids["doctor_id"],
            "appointment_date": "2026-10-15T10:00:00",
            "appointment_time": "10:00 AM",
            "status": "scheduled",
            "reason": "Test"
        }
        client.post(
            "/api/v1/appointments",
            headers=admin_headers,
            json=appointment_data
        )
        
        # Get by patient
        response = client.get(
            f"/api/v1/appointments?patient_id={ids['patient_id']}",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        for appt in data:
            assert appt["patient_id"] == ids["patient_id"]

    def test_get_appointments_by_doctor(self, client: TestClient, admin_headers,
                                         setup_patient_and_doctor):
        """Test filtering appointments by doctor"""
        ids = setup_patient_and_doctor
        
        # Create appointment
        appointment_data = {
            "patient_id": ids["patient_id"],
            "doctor_id": ids["doctor_id"],
            "appointment_date": "2026-10-15T10:00:00",
            "appointment_time": "10:00 AM",
            "status": "scheduled",
            "reason": "Test"
        }
        client.post(
            "/api/v1/appointments",
            headers=admin_headers,
            json=appointment_data
        )
        
        # Get by doctor
        response = client.get(
            f"/api/v1/appointments?doctor_id={ids['doctor_id']}",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        for appt in data:
            assert appt["doctor_id"] == ids["doctor_id"]

    def test_get_appointments_by_date(self, client: TestClient, admin_headers,
                                       setup_patient_and_doctor):
        """Test filtering appointments by date"""
        ids = setup_patient_and_doctor
        
        # Create appointment
        appointment_data = {
            "patient_id": ids["patient_id"],
            "doctor_id": ids["doctor_id"],
            "appointment_date": "2026-10-15T10:00:00",
            "appointment_time": "10:00 AM",
            "status": "scheduled",
            "reason": "Test"
        }
        client.post(
            "/api/v1/appointments",
            headers=admin_headers,
            json=appointment_data
        )
        
        # Get by date
        response = client.get(
            "/api/v1/appointments?date=2026-10-15T00:00:00",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    # ==========================================
    # UPDATE APPOINTMENT TESTS
    # ==========================================

    def test_update_appointment(self, client: TestClient, admin_headers,
                                  setup_patient_and_doctor):
        """Test updating an appointment"""
        ids = setup_patient_and_doctor
        
        # Create appointment
        appointment_data = {
            "patient_id": ids["patient_id"],
            "doctor_id": ids["doctor_id"],
            "appointment_date": "2026-10-15T10:00:00",
            "appointment_time": "10:00 AM",
            "status": "scheduled",
            "reason": "Original reason"
        }
        create_response = client.post(
            "/api/v1/appointments",
            headers=admin_headers,
            json=appointment_data
        )
        appointment_id = create_response.json()["id"]
        
        # Update appointment
        update_data = {
            "appointment_time": "11:00 AM",
            "reason": "Updated reason",
            "notes": "Added notes"
        }
        response = client.put(
            f"/api/v1/appointments/{appointment_id}",
            headers=admin_headers,
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["appointment_time"] == "11:00 AM"
        assert data["reason"] == "Updated reason"
        assert data["notes"] == "Added notes"

    def test_update_appointment_status(self, client: TestClient, admin_headers,
                                        setup_patient_and_doctor):
        """Test updating appointment status"""
        ids = setup_patient_and_doctor
        
        # Create appointment
        appointment_data = {
            "patient_id": ids["patient_id"],
            "doctor_id": ids["doctor_id"],
            "appointment_date": "2026-10-15T10:00:00",
            "appointment_time": "10:00 AM",
            "status": "scheduled",
            "reason": "Test"
        }
        create_response = client.post(
            "/api/v1/appointments",
            headers=admin_headers,
            json=appointment_data
        )
        appointment_id = create_response.json()["id"]
        
        # Update status
        response = client.patch(
            f"/api/v1/appointments/{appointment_id}/status",
            headers=admin_headers,
            json={"status": "confirmed"}
        )
        
        assert response.status_code == 200
        assert "confirmed" in response.text.lower()

    def test_update_appointment_status_cancelled(self, client: TestClient, 
                                                    admin_headers,
                                                    setup_patient_and_doctor):
        """Test cancelling an appointment"""
        ids = setup_patient_and_doctor
        
        # Create appointment
        appointment_data = {
            "patient_id": ids["patient_id"],
            "doctor_id": ids["doctor_id"],
            "appointment_date": "2026-10-15T10:00:00",
            "appointment_time": "10:00 AM",
            "status": "scheduled",
            "reason": "Test"
        }
        create_response = client.post(
            "/api/v1/appointments",
            headers=admin_headers,
            json=appointment_data
        )
        appointment_id = create_response.json()["id"]
        
        # Cancel appointment
        response = client.patch(
            f"/api/v1/appointments/{appointment_id}/status",
            headers=admin_headers,
            json={"status": "cancelled"}
        )
        
        assert response.status_code == 200
        
        # Verify status
        get_response = client.get(
            f"/api/v1/appointments/{appointment_id}",
            headers=admin_headers
        )
        assert get_response.json()["status"] == "cancelled"

    def test_update_appointment_status_completed(self, client: TestClient,
                                                    admin_headers,
                                                    setup_patient_and_doctor):
        """Test completing an appointment"""
        ids = setup_patient_and_doctor
        
        appointment_data = {
            "patient_id": ids["patient_id"],
            "doctor_id": ids["doctor_id"],
            "appointment_date": "2026-10-15T10:00:00",
            "appointment_time": "10:00 AM",
            "status": "confirmed",
            "reason": "Test"
        }
        create_response = client.post(
            "/api/v1/appointments",
            headers=admin_headers,
            json=appointment_data
        )
        appointment_id = create_response.json()["id"]
        
        response = client.patch(
            f"/api/v1/appointments/{appointment_id}/status",
            headers=admin_headers,
            json={"status": "completed"}
        )
        
        assert response.status_code == 200

    def test_update_nonexistent_appointment(self, client: TestClient, 
                                              admin_headers):
        """Test updating non-existent appointment"""
        update_data = {"appointment_time": "11:00 AM"}
        response = client.put(
            "/api/v1/appointments/99999",
            headers=admin_headers,
            json=update_data
        )
        assert response.status_code == 404

    # ==========================================
    # DELETE APPOINTMENT TESTS
    # ==========================================

    def test_delete_appointment(self, client: TestClient, admin_headers,
                                  setup_patient_and_doctor):
        """Test deleting an appointment"""
        ids = setup_patient_and_doctor
        
        # Create appointment
        appointment_data = {
            "patient_id": ids["patient_id"],
            "doctor_id": ids["doctor_id"],
            "appointment_date": "2026-10-15T10:00:00",
            "appointment_time": "10:00 AM",
            "status": "scheduled",
            "reason": "Test"
        }
        create_response = client.post(
            "/api/v1/appointments",
            headers=admin_headers,
            json=appointment_data
        )
        appointment_id = create_response.json()["id"]
        
        # Delete appointment
        response = client.delete(
            f"/api/v1/appointments/{appointment_id}",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        assert "deleted successfully" in response.text.lower()
        
        # Verify deleted
        get_response = client.get(
            f"/api/v1/appointments/{appointment_id}",
            headers=admin_headers
        )
        assert get_response.status_code == 404

    def test_delete_nonexistent_appointment(self, client: TestClient, 
                                              admin_headers):
        """Test deleting non-existent appointment"""
        response = client.delete(
            "/api/v1/appointments/99999",
            headers=admin_headers
        )
        assert response.status_code == 404

    def test_delete_appointment_unauthorized(self, client: TestClient, 
                                                auth_headers,
                                                setup_patient_and_doctor):
        """Test deleting appointment without admin privileges"""
        ids = setup_patient_and_doctor
        
        # Create appointment as admin
        appointment_data = {
            "patient_id": ids["patient_id"],
            "doctor_id": ids["doctor_id"],
            "appointment_date": "2026-10-15T10:00:00",
            "appointment_time": "10:00 AM",
            "status": "scheduled",
            "reason": "Test"
        }
        create_response = client.post(
            "/api/v1/appointments",
            headers=auth_headers,  # Regular user can create
            json=appointment_data
        )
        appointment_id = create_response.json()["id"]
        
        # Try to delete as regular user
        response = client.delete(
            f"/api/v1/appointments/{appointment_id}",
            headers=auth_headers
        )
        assert response.status_code == 403

    # ==========================================
    # APPOINTMENT STATUS TESTS
    # ==========================================

    def test_all_appointment_statuses(self, client: TestClient, admin_headers,
                                        setup_patient_and_doctor):
        """Test all valid appointment statuses"""
        ids = setup_patient_and_doctor
        statuses = ["scheduled", "confirmed", "in_progress", "completed", 
                    "cancelled", "no_show"]
        
        for status in statuses:
            appointment_data = {
                "patient_id": ids["patient_id"],
                "doctor_id": ids["doctor_id"],
                "appointment_date": "2026-10-15T10:00:00",
                "appointment_time": "10:00 AM",
                "status": status,
                "reason": f"Test appointment with status {status}"
            }
            
            response = client.post(
                "/api/v1/appointments",
                headers=admin_headers,
                json=appointment_data
            )
            
            assert response.status_code == 200, (
                f"Failed to create appointment with status '{status}': "
                f"{response.text}"
            )
            data = response.json()
            assert data["status"] == status
            assert data["patient_id"] == ids["patient_id"]
            assert data["doctor_id"] == ids["doctor_id"]