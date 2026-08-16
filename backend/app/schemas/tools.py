from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class SalesMetricsInput(BaseModel):
    site: str = "美国站"
    platform: str = "Amazon"
    start_date: date
    end_date: date
    category: str | None = None
    sku: str | None = None
    product_name: str | None = None
    granularity: Literal["month"] = "month"

    @model_validator(mode="after")
    def validate_dates(self):
        if self.start_date > self.end_date:
            raise ValueError("start_date must not be after end_date")
        return self


class SalesPeriod(BaseModel):
    period: str
    units_sold: int
    revenue: float
    cost: float
    gross_profit: float
    refund_units: int


class SalesMetricsOutput(BaseModel):
    site: str
    platform: str
    start_date: date
    end_date: date
    product_names: list[str]
    units_sold: int
    revenue: float
    cost: float
    gross_profit: float
    gross_margin_rate: float
    refund_units: int
    refund_rate: float
    series: list[SalesPeriod]


class InventoryStatusInput(BaseModel):
    site: str = "美国站"
    platform: str = "Amazon"
    as_of: date
    category: str | None = None
    sku: str | None = None
    product_name: str | None = None


class InventoryItem(BaseModel):
    sku: str
    product_name: str
    snapshot_date: date
    on_hand: int
    reserved: int
    inbound: int
    available: int


class InventoryStatusOutput(BaseModel):
    site: str
    platform: str
    as_of: date
    items: list[InventoryItem]


class SalesTrendInput(BaseModel):
    series: list[SalesPeriod] = Field(min_length=2)


class SalesTrendOutput(BaseModel):
    direction: Literal["growing", "stable", "declining"]
    overall_growth_rate: float
    latest_mom_rate: float
    periods: int


class InventoryPressureInput(BaseModel):
    available_units: int = Field(ge=0)
    inbound_units: int = Field(ge=0)
    average_daily_sales: float = Field(ge=0)


class InventoryPressureOutput(BaseModel):
    coverage_days: float | None
    pressure: Literal["stockout", "low", "healthy", "high", "overstock", "unknown"]
    rationale: str


class RestockInput(BaseModel):
    available_units: int = Field(ge=0)
    inbound_units: int = Field(ge=0)
    average_daily_sales: float = Field(ge=0)
    growth_rate: float = 0
    lead_time_days: int = Field(default=30, ge=1, le=180)
    target_coverage_days: int = Field(default=60, ge=7, le=365)
    safety_days: int = Field(default=15, ge=0, le=90)


class RestockOutput(BaseModel):
    should_restock: bool
    recommended_quantity: int
    target_demand: int
    rationale: str
    requires_human_confirmation: bool = True


class ImportBatchStatusInput(BaseModel):
    batch_id: str
    project_id: str


class ImportBatchStatusOutput(BaseModel):
    batch_id: str
    project_id: str
    status: str
    total_rows: int
    success_rows: int
    failed_rows: int
    error_message: str | None
