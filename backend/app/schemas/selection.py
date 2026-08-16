from datetime import date

from pydantic import BaseModel

from app.schemas.tools import (
    InventoryPressureOutput,
    InventoryStatusOutput,
    RestockOutput,
    SalesMetricsOutput,
    SalesTrendOutput,
)


class SelectionAnalysis(BaseModel):
    site: str
    platform: str
    start_date: date
    end_date: date
    product_names: list[str]
    sales: SalesMetricsOutput
    trend: SalesTrendOutput | None
    inventory: InventoryStatusOutput
    pressure: InventoryPressureOutput
    restock: RestockOutput
    average_daily_sales: float
    risks: list[str]
    evidence: list[str]
    human_confirmation_notice: str = "补货建议必须由人工确认，MVP 不执行真实采购。"
