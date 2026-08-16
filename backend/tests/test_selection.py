from fastapi.testclient import TestClient

from app.main import app


def _selection_context(client: TestClient):
    user = next(
        item for item in client.get("/api/v1/users").json() if item["display_name"] == "陈禾"
    )
    project = next(
        item
        for item in client.get("/api/v1/projects", params={"user_id": user["id"]}).json()
        if item["name"] == "健身器材选品计划"
    )
    return user, project


def test_simulation_exposes_growth_low_stock_decline_and_overstock() -> None:
    with TestClient(app) as client:
        user, project = _selection_context(client)
        rack = client.get(
            f"/api/v1/projects/{project['id']}/selection-overview",
            params={"user_id": user["id"], "product_name": "龙门架"},
        ).json()
        treadmill = client.get(
            f"/api/v1/projects/{project['id']}/selection-overview",
            params={"user_id": user["id"], "product_name": "跑步机"},
        ).json()
        dumbbell = client.get(
            f"/api/v1/projects/{project['id']}/selection-overview",
            params={"user_id": user["id"], "product_name": "哑铃"},
        ).json()

    assert rack["trend"]["direction"] == "growing"
    assert rack["pressure"]["pressure"] in {"stockout", "low"}
    assert rack["restock"]["recommended_quantity"] > 0
    assert rack["restock"]["requires_human_confirmation"] is True
    assert treadmill["trend"]["direction"] == "declining"
    assert treadmill["pressure"]["pressure"] == "overstock"
    assert treadmill["restock"]["recommended_quantity"] == 0
    assert dumbbell["sales"]["gross_margin_rate"] < 0.15


def test_follow_up_inherits_product_but_refreshes_decision_tools() -> None:
    with TestClient(app) as client:
        user, project = _selection_context(client)
        conversation = client.post(
            f"/api/v1/projects/{project['id']}/conversations",
            json={"user_id": user["id"], "title": "上下文继承测试"},
        ).json()
        first = client.post(
            f"/api/v1/conversations/{conversation['id']}/agent-runs",
            json={"user_id": user["id"], "content": "以每个月为周期分析龙门架的销售和库存"},
        )
        follow_up = client.post(
            f"/api/v1/conversations/{conversation['id']}/agent-runs",
            json={"user_id": user["id"], "content": "那么这个商品本月要不要增购？"},
        )
        messages = client.get(
            f"/api/v1/conversations/{conversation['id']}/messages",
            params={"user_id": user["id"]},
        ).json()

    assert first.status_code == 201
    assert follow_up.status_code == 201
    calls = follow_up.json()["tool_calls"]
    assert calls[0]["tool_name"] == "query_sales_metrics"
    assert calls[0]["input"]["product_name"] == "龙门架"
    assert {call["tool_name"] for call in calls} >= {
        "query_sales_metrics",
        "query_inventory_status",
        "calculate_inventory_pressure",
        "recommend_restock",
    }
    assert "必须由人工确认" in messages[-1]["content"]


def test_explicit_analysis_window_wins_over_decision_wording() -> None:
    with TestClient(app) as client:
        user, project = _selection_context(client)
        conversation = client.post(
            f"/api/v1/projects/{project['id']}/conversations",
            json={"user_id": user["id"], "title": "复合范围测试"},
        ).json()
        run = client.post(
            f"/api/v1/conversations/{conversation['id']}/agent-runs",
            json={
                "user_id": user["id"],
                "content": "分析最近18个月龙门架销售和库存，本月是否增购？",
            },
        ).json()

    assert [item["tool_name"] for item in run["tool_calls"]] == [
        "query_sales_metrics",
        "calculate_sales_trend",
        "query_inventory_status",
        "calculate_inventory_pressure",
        "recommend_restock",
    ]
