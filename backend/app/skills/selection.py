from datetime import date

from pydantic import BaseModel

from app.schemas.selection import SelectionAnalysis
from app.schemas.tools import (
    InventoryPressureOutput,
    InventoryStatusOutput,
    RestockOutput,
    SalesMetricsOutput,
    SalesTrendOutput,
)
from app.tools.registry import ToolRunner


def _run(
    runner: ToolRunner,
    outputs: list[tuple[str, dict]],
    tool_name: str,
    payload: dict,
) -> BaseModel:
    result = runner.run(tool_name, payload)
    outputs.append((tool_name, result.model_dump(mode="json")))
    return result


def _build_risks(
    sales: SalesMetricsOutput,
    trend: SalesTrendOutput | None,
    pressure: InventoryPressureOutput,
    inventory: InventoryStatusOutput,
    end_date: date,
) -> list[str]:
    risks: list[str] = []
    if not sales.series:
        risks.append("指定范围内没有销售事实，建议前需先补齐数据。")
    if sales.gross_margin_rate < 0.15:
        risks.append(f"毛利率仅 {sales.gross_margin_rate:.1%}，需评估促销和采购成本。")
    if sales.refund_rate >= 0.08:
        risks.append(f"退款率 {sales.refund_rate:.1%} 偏高，需先排查商品质量和描述。")
    if trend and trend.direction == "declining":
        risks.append("销量趋势下降，建议保守控制新增库存。")
    if pressure.pressure in {"stockout", "low"}:
        risks.append("库存覆盖偏低，存在断货风险。")
    if pressure.pressure in {"high", "overstock"}:
        risks.append("库存覆盖偏高，存在积压与资金占用风险。")
    if inventory.items:
        latest_snapshot = max(item.snapshot_date for item in inventory.items)
        if (end_date - latest_snapshot).days > 45:
            risks.append("库存快照超过 45 天，建议刷新后再决策。")
    else:
        risks.append("未找到可用库存快照。")
    return risks or ["未触发预置高风险阈值，仍需人工核对数据新鲜度。"]


def build_selection_analysis(
    scope: dict[str, str],
    sales: SalesMetricsOutput,
    trend: SalesTrendOutput | None,
    inventory: InventoryStatusOutput,
    pressure: InventoryPressureOutput,
    restock: RestockOutput,
    average_daily_sales: float,
) -> SelectionAnalysis:
    start_date = date.fromisoformat(scope["start_date"])
    end_date = date.fromisoformat(scope["end_date"])
    return SelectionAnalysis(
        site=scope["site"],
        platform=scope["platform"],
        start_date=start_date,
        end_date=end_date,
        product_names=sales.product_names,
        sales=sales,
        trend=trend,
        inventory=inventory,
        pressure=pressure,
        restock=restock,
        average_daily_sales=average_daily_sales,
        risks=_build_risks(sales, trend, pressure, inventory, end_date),
        evidence=[
            "query_sales_metrics 的销量、收入、毛利与退款结果",
            "query_inventory_status 的最新可用与在途库存",
            "calculate_sales_trend 与 calculate_inventory_pressure 的代码计算",
            "recommend_restock 的确定性覆盖天数规则",
        ],
    )


def run_selection_workflow(
    runner: ToolRunner, scope: dict[str, str]
) -> tuple[SelectionAnalysis, list[tuple[str, dict]]]:
    outputs: list[tuple[str, dict]] = []
    sales = SalesMetricsOutput.model_validate(
        _run(
            runner,
            outputs,
            "query_sales_metrics",
            {
                "site": scope["site"],
                "platform": scope["platform"],
                "start_date": scope["start_date"],
                "end_date": scope["end_date"],
                "category": scope.get("category"),
                "product_name": scope.get("product_name"),
                "granularity": "month",
            },
        )
    )
    trend = None
    if len(sales.series) >= 2:
        trend = SalesTrendOutput.model_validate(
            _run(
                runner,
                outputs,
                "calculate_sales_trend",
                {"series": [item.model_dump() for item in sales.series]},
            )
        )
    inventory = InventoryStatusOutput.model_validate(
        _run(
            runner,
            outputs,
            "query_inventory_status",
            {
                "site": scope["site"],
                "platform": scope["platform"],
                "as_of": scope["end_date"],
                "category": scope.get("category"),
                "product_name": scope.get("product_name"),
            },
        )
    )
    start_date = date.fromisoformat(scope["start_date"])
    end_date = date.fromisoformat(scope["end_date"])
    day_count = max(1, (end_date - start_date).days + 1)
    average_daily_sales = round(sales.units_sold / day_count, 4)
    available_units = sum(item.available for item in inventory.items)
    inbound_units = sum(item.inbound for item in inventory.items)
    pressure = InventoryPressureOutput.model_validate(
        _run(
            runner,
            outputs,
            "calculate_inventory_pressure",
            {
                "available_units": available_units,
                "inbound_units": inbound_units,
                "average_daily_sales": average_daily_sales,
            },
        )
    )
    growth_rate = trend.latest_mom_rate if trend else 0
    restock = RestockOutput.model_validate(
        _run(
            runner,
            outputs,
            "recommend_restock",
            {
                "available_units": available_units,
                "inbound_units": inbound_units,
                "average_daily_sales": average_daily_sales,
                "growth_rate": max(-0.5, min(0.5, growth_rate)),
                "lead_time_days": 30,
                "target_coverage_days": 60,
                "safety_days": 15,
            },
        )
    )
    analysis = build_selection_analysis(
        scope,
        sales,
        trend,
        inventory,
        pressure,
        restock,
        average_daily_sales,
    )
    return analysis, outputs


def render_selection_analysis(analysis: SelectionAnalysis) -> str:
    trend_text = (
        f"{analysis.trend.direction}，最近环比 {analysis.trend.latest_mom_rate:.1%}"
        if analysis.trend
        else "历史周期不足，暂无环比"
    )
    recommendation = (
        f"建议补货 {analysis.restock.recommended_quantity} 件"
        if analysis.restock.should_restock
        else "本月暂不建议增购"
    )
    product_text = "、".join(analysis.product_names) or "未匹配商品"
    risk_text = "\n".join(f"- {item}" for item in analysis.risks)
    evidence_text = "\n".join(f"- {item}" for item in analysis.evidence)
    return (
        "### 数据范围\n"
        f"{analysis.site} / {analysis.platform} / {analysis.start_date} 至 "
        f"{analysis.end_date} / {product_text}\n\n"
        "### 关键指标\n"
        f"销量 {analysis.sales.units_sold} 件，销售额 ${analysis.sales.revenue:,.2f}，"
        f"毛利率 {analysis.sales.gross_margin_rate:.1%}，"
        f"退款率 {analysis.sales.refund_rate:.1%}，趋势 {trend_text}。"
        f"库存压力 {analysis.pressure.pressure}，"
        f"覆盖天数 {analysis.pressure.coverage_days or 0:.1f} 天。\n\n"
        "### 建议\n"
        f"{recommendation}。{analysis.restock.rationale}\n\n"
        f"### 风险\n{risk_text}\n\n"
        f"### 调用依据\n{evidence_text}\n\n"
        f"> {analysis.human_confirmation_notice}"
    )
