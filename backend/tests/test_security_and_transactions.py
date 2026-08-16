from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import event, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.main import app
from app.models.analytics import SalesFact


def _users_and_sales_project(client: TestClient):
    users = client.get("/api/v1/users").json()
    artwork_user = next(item for item in users if item["display_name"] == "林然")
    sales_user = next(item for item in users if item["display_name"] == "周启")
    sales_project = next(
        item
        for item in client.get("/api/v1/projects", params={"user_id": sales_user["id"]}).json()
        if item["name"] == "美国站销售分析"
    )
    return artwork_user, sales_user, sales_project


def test_employee_cannot_read_another_departments_project() -> None:
    with TestClient(app) as client:
        artwork_user, _, sales_project = _users_and_sales_project(client)
        response = client.get(
            f"/api/v1/projects/{sales_project['id']}/conversations",
            params={"user_id": artwork_user["id"]},
        )
        visible_projects = client.get(
            "/api/v1/projects", params={"user_id": artwork_user["id"]}
        ).json()

    assert response.status_code == 403
    assert sales_project["id"] not in {item["id"] for item in visible_projects}


def test_import_database_failure_rolls_back_all_fact_rows() -> None:
    suffix = uuid4().hex[:8]
    content = (
        "sale_date,sku,product_name,category,site,platform,units_sold,revenue,cost,refund_units\n"
        f"2026-08-01,ROLLBACK-{suffix},回滚测试,健身器材,美国站,Amazon,10,1000,600,0\n"
    ).encode()

    with TestClient(app) as client:
        _, sales_user, sales_project = _users_and_sales_project(client)
        uploaded = client.post(
            "/api/v1/imports",
            data={
                "project_id": sales_project["id"],
                "user_id": sales_user["id"],
                "kind": "sales",
            },
            files={"file": ("rollback.csv", content, "text/csv")},
        ).json()
        batch_id = uploaded["batch"]["id"]

        def force_failure(session: Session, _flush_context, _instances) -> None:
            if any(
                isinstance(item, SalesFact) and item.import_batch_id == batch_id
                for item in session.new
            ):
                raise IntegrityError("forced test failure", {}, RuntimeError("forced"))

        event.listen(Session, "before_flush", force_failure)
        try:
            confirmed = client.post(
                f"/api/v1/imports/{batch_id}/confirm",
                json={"user_id": sales_user["id"]},
            )
        finally:
            event.remove(Session, "before_flush", force_failure)
        batch = client.get(
            f"/api/v1/imports/{batch_id}", params={"user_id": sales_user["id"]}
        ).json()

    with SessionLocal() as session:
        written_rows = session.scalar(
            select(func.count()).select_from(SalesFact).where(SalesFact.import_batch_id == batch_id)
        )

    assert confirmed.status_code == 500
    assert confirmed.json()["detail"] == "Import transaction rolled back"
    assert written_rows == 0
    assert batch["status"] == "failed"
