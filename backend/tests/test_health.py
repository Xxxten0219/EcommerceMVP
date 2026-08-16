from fastapi.testclient import TestClient

from app.api.v1 import health as health_module
from app.main import app


def test_health_check_reports_api_and_database() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "ecommerce-mvp-api",
        "version": "0.1.0",
        "database": "ok",
        "mock_mode": True,
    }


def test_health_check_reports_database_failure(monkeypatch) -> None:
    monkeypatch.setattr(health_module, "check_database_connection", lambda: False)

    with TestClient(app) as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 503
    assert response.json()["status"] == "degraded"
    assert response.json()["database"] == "unavailable"
