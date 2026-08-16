from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.agents.scope import resolve_scope
from app.db.session import get_session
from app.schemas.selection import SelectionAnalysis
from app.schemas.tools import (
    InventoryPressureInput,
    InventoryStatusInput,
    RestockInput,
    SalesMetricsInput,
    SalesTrendInput,
)
from app.services.access import require_project_access
from app.services.metrics import (
    calculate_inventory_pressure,
    calculate_sales_trend,
    query_inventory_status,
    query_sales_metrics,
    recommend_restock,
)
from app.skills.selection import build_selection_analysis

router = APIRouter(tags=["analytics"])
SessionDependency = Annotated[Session, Depends(get_session)]


@router.get("/projects/{project_id}/selection-overview", response_model=SelectionAnalysis)
def selection_overview(
    project_id: str,
    user_id: Annotated[str, Query()],
    session: SessionDependency,
    product_name: Annotated[str, Query(min_length=1)] = "龙门架",
) -> SelectionAnalysis:
    require_project_access(session, project_id, user_id)
    scope = resolve_scope(f"最近18个月{product_name}")
    sales = query_sales_metrics(
        session,
        SalesMetricsInput(
            site=scope["site"],
            platform=scope["platform"],
            start_date=scope["start_date"],
            end_date=scope["end_date"],
            category=scope.get("category"),
            product_name=scope.get("product_name"),
        ),
    )
    inventory = query_inventory_status(
        session,
        InventoryStatusInput(
            site=scope["site"],
            platform=scope["platform"],
            as_of=date.fromisoformat(scope["end_date"]),
            category=scope.get("category"),
            product_name=scope.get("product_name"),
        ),
    )
    trend = (
        calculate_sales_trend(SalesTrendInput(series=sales.series))
        if len(sales.series) >= 2
        else None
    )
    start_date = date.fromisoformat(scope["start_date"])
    end_date = date.fromisoformat(scope["end_date"])
    average_daily_sales = round(sales.units_sold / max(1, (end_date - start_date).days + 1), 4)
    available_units = sum(item.available for item in inventory.items)
    inbound_units = sum(item.inbound for item in inventory.items)
    pressure = calculate_inventory_pressure(
        InventoryPressureInput(
            available_units=available_units,
            inbound_units=inbound_units,
            average_daily_sales=average_daily_sales,
        )
    )
    restock = recommend_restock(
        RestockInput(
            available_units=available_units,
            inbound_units=inbound_units,
            average_daily_sales=average_daily_sales,
            growth_rate=max(-0.5, min(0.5, trend.latest_mom_rate if trend else 0)),
        )
    )
    return build_selection_analysis(
        scope, sales, trend, inventory, pressure, restock, average_daily_sales
    )
