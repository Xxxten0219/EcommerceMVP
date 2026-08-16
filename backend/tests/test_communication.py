from fastapi.testclient import TestClient

from app.main import app


def _demo_user_and_project(client: TestClient, display_name: str, project_name: str):
    user = next(
        item for item in client.get("/api/v1/users").json() if item["display_name"] == display_name
    )
    project = next(
        item
        for item in client.get("/api/v1/projects", params={"user_id": user["id"]}).json()
        if item["name"] == project_name
    )
    return user, project


def test_conversations_have_independent_message_histories() -> None:
    with TestClient(app) as client:
        user, project = _demo_user_and_project(client, "周启", "美国站销售分析")
        first = client.post(
            f"/api/v1/projects/{project['id']}/conversations",
            json={"user_id": user["id"], "title": "月度复盘"},
        ).json()
        second = client.post(
            f"/api/v1/projects/{project['id']}/conversations",
            json={"user_id": user["id"], "title": "退款分析"},
        ).json()

        client.post(
            f"/api/v1/conversations/{first['id']}/messages",
            json={"user_id": user["id"], "content": "分析龙门架"},
        )
        first_messages = client.get(
            f"/api/v1/conversations/{first['id']}/messages", params={"user_id": user["id"]}
        ).json()
        second_messages = client.get(
            f"/api/v1/conversations/{second['id']}/messages", params={"user_id": user["id"]}
        ).json()

    assert [message["content"] for message in first_messages] == ["分析龙门架"]
    assert second_messages == []


def test_conversation_can_be_renamed_and_context_is_built() -> None:
    with TestClient(app) as client:
        user, project = _demo_user_and_project(client, "陈禾", "健身器材选品计划")
        conversation = client.post(
            f"/api/v1/projects/{project['id']}/conversations",
            json={"user_id": user["id"], "title": "新聊天"},
        ).json()
        renamed = client.patch(
            f"/api/v1/conversations/{conversation['id']}",
            json={"user_id": user["id"], "title": "龙门架补货"},
        )
        context = client.get(
            f"/api/v1/conversations/{conversation['id']}/context",
            params={"user_id": user["id"]},
        )

    assert renamed.status_code == 200
    assert renamed.json()["title"] == "龙门架补货"
    assert context.status_code == 200
    assert isinstance(context.json()["structured_scope"], dict)
