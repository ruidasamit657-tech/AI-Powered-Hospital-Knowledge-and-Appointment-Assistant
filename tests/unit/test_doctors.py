"""
Unit tests for doctor endpoints
"""

from fastapi.testclient import TestClient

class TestDoctors:
    """Test doctor CRUD operations"""
    
    def test_create_doctor(self, client: TestClient, admin_headers, sample_doctor_data, sample_department_data):
        """Test creating a doctor"""
        # Create department first
        dept_response = client.post(
            "/api/v1/departments",
            headers=admin_headers,
            json=sample_department_data
        )
        department_id = dept_response.json()["id"]
        sample_doctor_data["department_id"] = department_id
        
        response = client.post(
            "/api/v1/doctors",
            headers=admin_headers,
            json=sample_doctor_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == sample_doctor_data["first_name"]
        assert data["last_name"] == sample_doctor_data["last_name"]
        assert data["email"] == sample_doctor_data["email"]
        assert data["specialization"] == sample_doctor_data["specialization"]
        assert "id" in data

    def test_get_doctors(self, client: TestClient, auth_headers):
        """Test getting all doctors"""
        response = client.get(
            "/api/v1/doctors",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_doctors_by_department(self, client: TestClient, auth_headers, admin_headers, sample_doctor_data, sample_department_data):
        """Test filtering doctors by department"""
        # Create department
        dept_response = client.post(
            "/api/v1/departments",
            headers=admin_headers,
            json=sample_department_data
        )
        department_id = dept_response.json()["id"]
        
        # Create doctor
        sample_doctor_data["department_id"] = department_id
        client.post(
            "/api/v1/doctors",
            headers=admin_headers,
            json=sample_doctor_data
        )
        
        # Get doctors by department
        response = client.get(
            f"/api/v1/doctors?department_id={department_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if data:
            assert data[0]["department_id"] == department_id

    def test_update_doctor(self, client: TestClient, admin_headers, sample_doctor_data, sample_department_data):
        """Test updating a doctor"""
        # Create department and doctor
        dept_response = client.post(
            "/api/v1/departments",
            headers=admin_headers,
            json=sample_department_data
        )
        sample_doctor_data["department_id"] = dept_response.json()["id"]
        
        create_response = client.post(
            "/api/v1/doctors",
            headers=admin_headers,
            json=sample_doctor_data
        )
        doctor_id = create_response.json()["id"]
        
        # Update doctor
        update_data = {
            "experience_years": 15,
            "bio": "Updated bio for testing"
        }
        response = client.put(
            f"/api/v1/doctors/{doctor_id}",
            headers=admin_headers,
            json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["experience_years"] == 15
        assert data["bio"] == "Updated bio for testing"