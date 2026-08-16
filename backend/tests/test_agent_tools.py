from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.schemas.tools import SalesMetricsInput
from app.tools.registry import TOOL_REGISTRY


def _selection_context(client: TestClient):
    user = next(
        item for item in client.get("/api/v1/users").json() if item["display_name"] == "陈禾"
    )
    project = next(
        item
        for item in client.get("/api/v1/projects", params={"user_id": user["id"]}).json()
        if item["name"] == "健身器材选品计划"
    )
    conversation = client.post(
        f"/api/v1/projects/{project['id']}/conversations",
        json={"user_id": user["id"], "title": "Agent 工具测试"},
    ).json()
    return user, conversation


def test_registered_tools_are_explicit_and_inputs_validate() -> None:
    assert set(TOOL_REGISTRY) == {
        "query_sales_metrics",
        "query_inventory_status",
        "calculate_sales_trend",
        "calculate_inventory_pressure",
        "recommend_restock",
        "get_import_batch_status",
    }
    try:
        SalesMetricsInput(start_date="2026-08-02", end_date="2026-08-01")
    except ValidationError as error:
        assert "start_date must not be after end_date" in str(error)
    else:
        raise AssertionError("Reversed date range must be rejected")


def test_agent_run_uses_controlled_tools_and_persists_trace() -> None:
    with TestClient(app) as client:
        user, conversation = _selection_context(client)
        response = client.post(
            f"/api/v1/conversations/{conversation['id']}/agent-runs",
            json={"user_id": user["id"], "content": "分析最近18个月龙门架的销售和库存"},
        )
        payload = response.json()
        trace = client.get(
            f"/api/v1/agent-runs/{payload['id']}/tool-calls",
            params={"user_id": user["id"]},
        )

    assert response.status_code == 201
    assert payload["status"] == "completed"
    assert payload["provider"] == "mock"
    assert [item["tool_name"] for item in payload["tool_calls"]] == [
        "query_sales_metrics",
        "calculate_sales_trend",
        "query_inventory_status",
        "calculate_inventory_pressure",
        "recommend_restock",
    ]
    assert trace.status_code == 200
    assert all(item["status"] == "succeeded" for item in trace.json())
    assert all(item["duration_ms"] >= 0 for item in trace.json())
    assert trace.json()[0]["input"]["product_name"] == "龙门架"
    assert trace.json()[0]["output_summary"]["units_sold"] > 0
