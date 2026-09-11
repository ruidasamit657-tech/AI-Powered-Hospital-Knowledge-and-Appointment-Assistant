"""
Unit tests for department endpoints
"""

from fastapi.testclient import TestClient

class TestDepartments:
    """Test department CRUD operations"""
    
    def test_create_department(self, client: TestClient, admin_headers, sample_department_data):
        """Test creating a department (admin only)"""
        response = client.post(
            "/api/v1/departments",
            headers=admin_headers,
            json=sample_department_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_department_data["name"]
        assert data["description"] == sample_department_data["description"]
        assert data["location"] == sample_department_data["location"]
        assert data["phone"] == sample_department_data["phone"]
        assert data["head_of_department"] == sample_department_data["head_of_department"]
        assert "id" in data
        assert "created_at" in data

    def test_create_department_unauthorized(self, client: TestClient, auth_headers, sample_department_data):
        """Test creating department without admin privileges"""
        response = client.post(
            "/api/v1/departments",
            headers=auth_headers,
            json=sample_department_data
        )
        assert response.status_code == 403

    def test_create_duplicate_department(self, client: TestClient, admin_headers, sample_department_data):
        """Test creating department with duplicate name"""
        # First creation
        client.post(
            "/api/v1/departments",
            headers=admin_headers,
            json=sample_department_data
        )
        
        # Second creation with same name
        response = client.post(
            "/api/v1/departments",
            headers=admin_headers,
            json=sample_department_data
        )
        assert response.status_code == 400
        assert "Department with this name already exists" in response.text

    def test_get_departments(self, client: TestClient, auth_headers, admin_headers, sample_department_data):
        """Test getting all departments"""
        # Create a department first
        client.post(
            "/api/v1/departments",
            headers=admin_headers,
            json=sample_department_data
        )
        
        response = client.get(
            "/api/v1/departments",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "id" in data[0]
        assert "name" in data[0]

    def test_get_specific_department(self, client: TestClient, auth_headers, admin_headers, sample_department_data):
        """Test getting a specific department"""
        # Create department
        create_response = client.post(
            "/api/v1/departments",
            headers=admin_headers,
            json=sample_department_data
        )
        department_id = create_response.json()["id"]
        
        # Get specific department
        response = client.get(
            f"/api/v1/departments/{department_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == department_id
        assert data["name"] == sample_department_data["name"]

    def test_get_nonexistent_department(self, client: TestClient, auth_headers):
        """Test getting non-existent department"""
        response = client.get(
            "/api/v1/departments/99999",
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_update_department(self, client: TestClient, admin_headers, sample_department_data):
        """Test updating a department"""
        # Create department
        create_response = client.post(
            "/api/v1/departments",
            headers=admin_headers,
            json=sample_department_data
        )
        department_id = create_response.json()["id"]
        
        # Update department
        update_data = {
            "phone": "555-9999",
            "head_of_department": "Dr. Updated"
        }
        response = client.put(
            f"/api/v1/departments/{department_id}",
            headers=admin_headers,
            json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["phone"] == "555-9999"
        assert data["head_of_department"] == "Dr. Updated"

    def test_delete_department(self, client: TestClient, admin_headers, sample_department_data):
        """Test deleting a department"""
        # Create department
        create_response = client.post(
            "/api/v1/departments",
            headers=admin_headers,
            json=sample_department_data
        )
        department_id = create_response.json()["id"]
        
        # Delete department
        response = client.delete(
            f"/api/v1/departments/{department_id}",
            headers=admin_headers
        )
        assert response.status_code == 200
        assert "Department deleted successfully" in response.text
        
        # Verify it's deleted
        get_response = client.get(
            f"/api/v1/departments/{department_id}",
            headers=admin_headers
        )
        assert get_response.status_code == 404