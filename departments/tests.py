import pytest
from rest_framework.test import APIClient
from rest_framework import status
from .models import Department, Employee


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
class TestDepartmentLogic:

    def test_unique_name_per_parent(self, api_client):
        parent = Department.objects.create(name="Parent")
        child = Department.objects.create(name="Child", parent=parent)
        response = api_client.post("/departments/", {"name": child.name, "parent_id": parent.id})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_prevent_self_parenting(self, api_client):
        parent = Department.objects.create(name="Parent")
        response = api_client.patch(f"/departments/{parent.id}/", {"parent_id": parent.id})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "cannot be its own parent" in str(response.data)

    def test_cycle_detection_conflict(self, api_client):
        parent = Department.objects.create(name="Parent")
        child = Department.objects.create(name="Child", parent=parent)
        response = api_client.patch(f"/departments/{parent.id}/", {"parent_id": child.id})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Cycle detected" in str(response.data)

    def test_recursion_depth_limit(self, api_client):
        parent = Department.objects.create(name="Parent")
        child = Department.objects.create(name="Child 1", parent=parent)
        Department.objects.create(name="Child 2", parent=child)
        response = api_client.get(f"/departments/{parent.id}/?depth=1")
        assert len(response.data["children"]) == 1
        assert response.data["children"][0]["children"] == []

    def test_employee_creation_404(self, api_client):
        response = api_client.post("/departments/9999/employees/", {
            "full_name": "Full Name",
            "position": "Position",
        })
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_cascade(self, api_client):
        parent = Department.objects.create(name="Parent")
        Department.objects.create(name="Child", parent=parent)

        api_client.delete(f"/departments/{parent.id}/")
        assert not Department.objects.filter(name="Child").exists()

    def test_delete_reassign(self, api_client):
        parent = Department.objects.create(name="Parent")
        child = Department.objects.create(name="Child", parent=parent)
        employee = Employee.objects.create(full_name="Employee", department=child)
        new_parent = Department.objects.create(name="New Parent")
        response = api_client.delete(f"/departments/{child.id}/?mode=reassign&reassign_to_department_id={new_parent.id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Department.objects.count() == 2
        assert Employee.objects.count() == 1
        assert Employee.objects.get(full_name=employee.full_name).department == new_parent

    def test_name_trimming(self, api_client):
        response = api_client.post("/departments/", {"name": "  Parent  "})
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Parent"
        assert Department.objects.get(name="Parent").name == "Parent"
