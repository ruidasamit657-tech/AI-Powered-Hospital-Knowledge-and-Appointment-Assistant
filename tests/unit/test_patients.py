"""
Unit tests for patient endpoints
"""

from fastapi.testclient import TestClient


class TestPatients:
    """Test patient CRUD operations"""

    def test_create_patient(self, client: TestClient, admin_headers, sample_patient_data):
        """Test creating a patient"""
        response = client.post(
            "/api/v1/patients",
            headers=admin_headers,
            json=sample_patient_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == sample_patient_data["first_name"]
        assert data["last_name"] == sample_patient_data["last_name"]
        assert data["email"] == sample_patient_data["email"]
        assert data["blood_type"] == sample_patient_data["blood_type"]
        assert "id" in data

    def test_get_patients(self, client: TestClient, auth_headers):
        """Test getting all patients"""
        response = client.get(
            "/api/v1/patients",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_specific_patient(self, client: TestClient, admin_headers, sample_patient_data):
        """Test getting a specific patient"""
        # Create patient
        create_response = client.post(
            "/api/v1/patients",
            headers=admin_headers,
            json=sample_patient_data
        )
        patient_id = create_response.json()["id"]

        # Get patient
        response = client.get(
            f"/api/v1/patients/{patient_id}",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == patient_id
        assert data["first_name"] == sample_patient_data["first_name"]

    def test_update_patient(self, client: TestClient, admin_headers, sample_patient_data):
        """Test updating a patient"""
        # Create patient
        create_response = client.post(
            "/api/v1/patients",
            headers=admin_headers,
            json=sample_patient_data
        )
        patient_id = create_response.json()["id"]

        # Update patient
        update_data = {
            "phone": "555-9999",
            "blood_type": "AB-"
        }
        response = client.put(
            f"/api/v1/patients/{patient_id}",
            headers=admin_headers,
            json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["phone"] == "555-9999"
        assert data["blood_type"] == "AB-"