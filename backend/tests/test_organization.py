from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def test_demo_organization_is_seeded_and_projects_are_filtered() -> None:
    with TestClient(app) as client:
        departments = client.get("/api/v1/departments").json()
        users = client.get("/api/v1/users").json()

        sales_department = next(item for item in departments if item["code"] == "sales")
        sales_user = next(item for item in users if item["display_name"] == "周启")
        response = client.get(
            "/api/v1/projects",
            params={"user_id": sales_user["id"], "department_id": sales_department["id"]},
        )

    assert response.status_code == 200
    assert [project["name"] for project in response.json()] == ["美国站销售分析"]
    assert all(project["department_id"] == sales_department["id"] for project in response.json())


def test_admin_can_create_employee_and_assign_project() -> None:
    suffix = uuid4().hex[:8]
    with TestClient(app) as client:
        departments = client.get("/api/v1/departments").json()
        users = client.get("/api/v1/users").json()
        artwork = next(item for item in departments if item["code"] == "artwork")
        admin = next(item for item in users if item["role"] == "admin")

        employee_response = client.post(
            "/api/v1/users",
            json={
                "department_id": artwork["id"],
                "display_name": f"测试美工-{suffix}",
                "role": "employee",
            },
        )
        employee = employee_response.json()
        project_response = client.post(
            "/api/v1/projects",
            json={
                "department_id": artwork["id"],
                "name": f"测试项目-{suffix}",
                "description": "M1 integration test",
                "created_by": admin["id"],
                "member_ids": [employee["id"]],
            },
        )

    assert employee_response.status_code == 201
    assert project_response.status_code == 201
    assert employee["id"] in project_response.json()["member_ids"]
