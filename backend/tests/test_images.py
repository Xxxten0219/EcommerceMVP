import hashlib
from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from app.db.session import SessionLocal
from app.main import app
from app.models.communication import Attachment


def _artwork_context(client: TestClient):
    user = next(
        item for item in client.get("/api/v1/users").json() if item["display_name"] == "林然"
    )
    project = next(
        item
        for item in client.get("/api/v1/projects", params={"user_id": user["id"]}).json()
        if item["name"] == "龙门架主图优化"
    )
    conversation = client.post(
        f"/api/v1/projects/{project['id']}/conversations",
        json={"user_id": user["id"], "title": "图片版本测试"},
    ).json()
    return user, project, conversation


def _png_bytes() -> bytes:
    output = BytesIO()
    Image.new("RGB", (640, 480), (65, 89, 118)).save(output, format="PNG")
    return output.getvalue()


def _upload(client: TestClient, user: dict, project: dict, conversation: dict) -> dict:
    response = client.post(
        "/api/v1/image-assets",
        data={
            "project_id": project["id"],
            "conversation_id": conversation["id"],
            "user_id": user["id"],
        },
        files={"file": ("rack-source.png", _png_bytes(), "image/png")},
    )
    assert response.status_code == 201
    return response.json()


def test_image_versions_never_overwrite_source_and_can_chain() -> None:
    with TestClient(app) as client:
        user, project, conversation = _artwork_context(client)
        source = _upload(client, user, project, conversation)
        original_digest = hashlib.sha256(_png_bytes()).hexdigest()
        first = client.post(
            "/api/v1/image-versions",
            json={
                "user_id": user["id"],
                "conversation_id": conversation["id"],
                "source_attachment_id": source["id"],
                "prompt": "提亮主体，增强立体感",
            },
        ).json()
        second = client.post(
            "/api/v1/image-versions",
            json={
                "user_id": user["id"],
                "conversation_id": conversation["id"],
                "source_attachment_id": source["id"],
                "parent_version_id": first["id"],
                "prompt": "在上一版基础上增加冷色商业风格",
            },
        ).json()
        generated = client.get(
            f"/api/v1/attachments/{second['output_attachment_id']}/content",
            params={"user_id": user["id"]},
        )

    with SessionLocal() as session:
        source_record = session.get(Attachment, source["id"])
        first_output = session.get(Attachment, first["output_attachment_id"])
        second_output = session.get(Attachment, second["output_attachment_id"])
        assert source_record is not None
        assert first_output is not None
        assert second_output is not None
        stored_digest = hashlib.sha256(Path(source_record.storage_path).read_bytes()).hexdigest()
        assert stored_digest == original_digest
        storage_paths = {
            source_record.storage_path,
            first_output.storage_path,
            second_output.storage_path,
        }
        assert len(storage_paths) == 3

    assert first["status"] == "completed"
    assert second["status"] == "completed"
    assert second["parent_version_id"] == first["id"]
    assert generated.status_code == 200
    assert generated.headers["content-type"] == "image/png"


def test_failed_image_request_is_preserved_and_retryable() -> None:
    with TestClient(app) as client:
        user, project, conversation = _artwork_context(client)
        source = _upload(client, user, project, conversation)
        failed = client.post(
            "/api/v1/image-versions",
            json={
                "user_id": user["id"],
                "conversation_id": conversation["id"],
                "source_attachment_id": source["id"],
                "prompt": "[mock-fail-once] 模拟失败后重试",
            },
        ).json()
        retried = client.post(
            f"/api/v1/image-versions/{failed['id']}/retry",
            json={"user_id": user["id"]},
        ).json()
        history = client.get(
            f"/api/v1/conversations/{conversation['id']}/image-versions",
            params={"user_id": user["id"]},
        ).json()

    assert failed["status"] == "failed"
    assert failed["error_message"]
    assert retried["status"] == "completed"
    assert retried["retry_count"] == 2
    assert retried["prompt"] == failed["prompt"]
    assert history[-1]["id"] == failed["id"]
