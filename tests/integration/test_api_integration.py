"""
Integration tests for the complete API flow
"""

# pylint: disable=unused-import
import pytest  # Kept for test suite discovery structures
# pylint: enable=unused-import
from fastapi.testclient import TestClient


class TestAPIIntegration:
    """Test complete API workflows"""
    
    def test_complete_workflow(self, client: TestClient):
        """Test complete CRUD workflow"""
        
        # 1. Register user
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "integration@example.com",
                "username": "integration_user",
                "full_name": "Integration User",
                "password": "Test123!",
                "role": "admin"
            }
        )
        assert register_response.status_code == 200
        
        # 2. Login
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "integration_user",
                "password": "Test123!"
            }
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 3. Create department
        dept_data = {
            "name": "Integration Cardiology",
            "description": "Integration test department",
            "location": "Floor 3",
            "phone": "555-9999",
            "head_of_department": "Dr. Integration"
        }
        dept_response = client.post(
            "/api/v1/departments",
            headers=headers,
            json=dept_data
        )
        assert dept_response.status_code == 200
        department_id = dept_response.json()["id"]
        
        # 4. Create doctor
        doctor_data = {
            "first_name": "Integration",
            "last_name": "Doctor",
            "email": "integration.doctor@hospital.com",
            "phone": "555-8888",
            "specialization": "Cardiologist",
            "qualifications": ["MD"],
            "experience_years": 10,
            "department_id": department_id,
            "available_days": ["Monday"],
            "available_hours": ["09:00-12:00"],
            "is_active": "active",
            "bio": "Integration test doctor"
        }
        doctor_response = client.post(
            "/api/v1/doctors",
            headers=headers,
            json=doctor_data
        )
        assert doctor_response.status_code == 200
        doctor_id = doctor_response.json()["id"]
        
        # 5. Create patient
        patient_data = {
            "first_name": "Integration",
            "last_name": "Patient",
            "email": "integration.patient@email.com",
            "phone": "555-7777",
            "date_of_birth": "1980-01-01",
            "gender": "Male",
            "blood_type": "O+",
            "allergies": ["None"]
        }
        patient_response = client.post(
            "/api/v1/patients",
            headers=headers,
            json=patient_data
        )
        assert patient_response.status_code == 200
        patient_id = patient_response.json()["id"]
        
        # 6. Create appointment
        appointment_data = {
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "appointment_date": "2026-10-01T10:00:00",
            "appointment_time": "10:00 AM",
            "status": "scheduled",
            "reason": "Integration test appointment",
            "notes": "Created during integration test"
        }
        appointment_response = client.post(
            "/api/v1/appointments",
            headers=headers,
            json=appointment_data
        )
        assert appointment_response.status_code == 200
        appointment_id = appointment_response.json()["id"]
        
        # 7. Get all data
        departments = client.get("/api/v1/departments", headers=headers)
        assert departments.status_code == 200
        
        doctors = client.get("/api/v1/doctors", headers=headers)
        assert doctors.status_code == 200
        
        patients = client.get("/api/v1/patients", headers=headers)
        assert patients.status_code == 200
        
        appointments = client.get("/api/v1/appointments", headers=headers)
        assert appointments.status_code == 200
        
        # 8. Update appointment status
        status_response = client.patch(
            f"/api/v1/appointments/{appointment_id}/status",
            headers=headers,
            json={"status": "confirmed"}
        )
        assert status_response.status_code == 200
        
        # 9. Delete all test data
        client.delete(f"/api/v1/appointments/{appointment_id}", headers=headers)
        client.delete(f"/api/v1/patients/{patient_id}", headers=headers)
        client.delete(f"/api/v1/doctors/{doctor_id}", headers=headers)
        client.delete(f"/api/v1/departments/{department_id}", headers=headers)
        
        # 10. Verify deletions
        get_dept = client.get(f"/api/v1/departments/{department_id}", headers=headers)
        assert get_dept.status_code == 404

    def test_chat_with_knowledge_base(self, client: TestClient, auth_headers):
        """Test chat with knowledge base"""
        # Try to get hospital information
        response = client.post(
            "/api/v1/chat",
            headers=auth_headers,
            json={
                "question": "What are the hospital visiting hours?",
                "use_groq": False,
                "include_sources": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert data.get("is_emergency") is False
