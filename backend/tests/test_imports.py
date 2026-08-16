from io import BytesIO
from uuid import uuid4

from fastapi.testclient import TestClient
from openpyxl import Workbook

from app.main import app


def _sales_user_and_project(client: TestClient):
    user = next(
        item for item in client.get("/api/v1/users").json() if item["display_name"] == "周启"
    )
    project = next(
        item
        for item in client.get("/api/v1/projects", params={"user_id": user["id"]}).json()
        if item["name"] == "美国站销售分析"
    )
    return user, project


def test_csv_import_preview_errors_confirmation_and_duplicate_detection() -> None:
    suffix = uuid4().hex[:8]
    csv_content = (
        "sale_date,sku,product_name,category,site,platform,units_sold,revenue,cost,refund_units\n"
        f"2026-08-01,TEST-{suffix},测试商品,健身器材,美国站,Amazon,10,1000.00,600.00,1\n"
        f"bad-date,TEST-BAD-{suffix},坏数据,健身器材,美国站,Amazon,4,400.00,200.00,0\n"
    ).encode()

    with TestClient(app) as client:
        user, project = _sales_user_and_project(client)
        form = {"project_id": project["id"], "user_id": user["id"], "kind": "sales"}
        upload = client.post(
            "/api/v1/imports",
            data=form,
            files={"file": ("sales.csv", csv_content, "text/csv")},
        )
        batch_id = upload.json()["batch"]["id"]
        errors = client.get(
            f"/api/v1/imports/{batch_id}/errors.csv", params={"user_id": user["id"]}
        )
        confirmed = client.post(f"/api/v1/imports/{batch_id}/confirm", json={"user_id": user["id"]})
        duplicate = client.post(
            "/api/v1/imports",
            data=form,
            files={"file": ("sales-copy.csv", csv_content, "text/csv")},
        )

    assert upload.status_code == 201
    assert upload.json()["batch"]["success_rows"] == 1
    assert upload.json()["batch"]["failed_rows"] == 1
    assert "invalid_format" in errors.text
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "completed"
    assert duplicate.status_code == 409


def test_xlsx_inventory_file_is_supported() -> None:
    suffix = uuid4().hex[:8]
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(
        [
            "snapshot_date",
            "sku",
            "product_name",
            "category",
            "site",
            "platform",
            "on_hand",
            "reserved",
            "inbound",
        ]
    )
    sheet.append(
        [
            "2026-08-15",
            f"INV-{suffix}",
            "库存测试",
            "健身器材",
            "美国站",
            "Amazon",
            50,
            5,
            20,
        ]
    )
    content = BytesIO()
    workbook.save(content)

    with TestClient(app) as client:
        user, project = _sales_user_and_project(client)
        response = client.post(
            "/api/v1/imports",
            data={"project_id": project["id"], "user_id": user["id"], "kind": "inventory"},
            files={
                "file": (
                    "inventory.xlsx",
                    content.getvalue(),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
        )

    assert response.status_code == 201
    assert response.json()["batch"]["success_rows"] == 1
    assert response.json()["batch"]["failed_rows"] == 0
