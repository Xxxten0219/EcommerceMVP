from collections import defaultdict
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.analytics import InventorySnapshot, Product, SalesFact
from app.schemas.tools import (
    InventoryItem,
    InventoryPressureInput,
    InventoryPressureOutput,
    InventoryStatusInput,
    InventoryStatusOutput,
    RestockInput,
    RestockOutput,
    SalesMetricsInput,
    SalesMetricsOutput,
    SalesPeriod,
    SalesTrendInput,
    SalesTrendOutput,
)


def _product_filters(statement, input_data):
    statement = statement.where(
        Product.site == input_data.site,
        Product.platform == input_data.platform,
    )
    if input_data.category:
        statement = statement.where(Product.category.contains(input_data.category))
    if input_data.sku:
        statement = statement.where(Product.sku == input_data.sku)
    if input_data.product_name:
        statement = statement.where(Product.name.contains(input_data.product_name))
    return statement


def query_sales_metrics(session: Session, input_data: SalesMetricsInput) -> SalesMetricsOutput:
    statement = (
        select(Product, SalesFact)
        .join(SalesFact, SalesFact.product_id == Product.id)
        .where(SalesFact.sale_date.between(input_data.start_date, input_data.end_date))
    )
    rows = session.execute(_product_filters(statement, input_data)).all()
    series: dict[str, dict[str, Decimal | int]] = defaultdict(
        lambda: {
            "units": 0,
            "revenue": Decimal("0"),
            "cost": Decimal("0"),
            "refunds": 0,
        }
    )
    product_names: set[str] = set()
    for product, fact in rows:
        product_names.add(product.name)
        period = fact.sale_date.strftime("%Y-%m")
        series[period]["units"] += fact.units_sold
        series[period]["revenue"] += fact.revenue
        series[period]["cost"] += fact.cost
        series[period]["refunds"] += fact.refund_units

    periods = [
        SalesPeriod(
            period=period,
            units_sold=int(values["units"]),
            revenue=float(values["revenue"]),
            cost=float(values["cost"]),
            gross_profit=float(values["revenue"] - values["cost"]),
            refund_units=int(values["refunds"]),
        )
        for period, values in sorted(series.items())
    ]
    units = sum(period.units_sold for period in periods)
    revenue = sum(period.revenue for period in periods)
    cost = sum(period.cost for period in periods)
    refunds = sum(period.refund_units for period in periods)
    profit = revenue - cost
    return SalesMetricsOutput(
        site=input_data.site,
        platform=input_data.platform,
        start_date=input_data.start_date,
        end_date=input_data.end_date,
        product_names=sorted(product_names),
        units_sold=units,
        revenue=round(revenue, 2),
        cost=round(cost, 2),
        gross_profit=round(profit, 2),
        gross_margin_rate=round(profit / revenue, 4) if revenue else 0,
        refund_units=refunds,
        refund_rate=round(refunds / units, 4) if units else 0,
        series=periods,
    )


def query_inventory_status(
    session: Session, input_data: InventoryStatusInput
) -> InventoryStatusOutput:
    statement = (
        select(Product, InventorySnapshot)
        .join(InventorySnapshot, InventorySnapshot.product_id == Product.id)
        .where(InventorySnapshot.snapshot_date <= input_data.as_of)
        .order_by(InventorySnapshot.snapshot_date.desc())
    )
    rows = session.execute(_product_filters(statement, input_data)).all()
    latest: dict[str, InventoryItem] = {}
    for product, snapshot in rows:
        if product.id in latest:
            continue
        latest[product.id] = InventoryItem(
            sku=product.sku,
            product_name=product.name,
            snapshot_date=snapshot.snapshot_date,
            on_hand=snapshot.on_hand,
            reserved=snapshot.reserved,
            inbound=snapshot.inbound,
            available=max(0, snapshot.on_hand - snapshot.reserved),
        )
    return InventoryStatusOutput(
        site=input_data.site,
        platform=input_data.platform,
        as_of=input_data.as_of,
        items=sorted(latest.values(), key=lambda item: item.sku),
    )


def calculate_sales_trend(input_data: SalesTrendInput) -> SalesTrendOutput:
    first = input_data.series[0].units_sold
    latest = input_data.series[-1].units_sold
    previous = input_data.series[-2].units_sold
    overall_rate = (latest - first) / first if first else 0
    latest_rate = (latest - previous) / previous if previous else 0
    if overall_rate > 0.08:
        direction = "growing"
    elif overall_rate < -0.08:
        direction = "declining"
    else:
        direction = "stable"
    return SalesTrendOutput(
        direction=direction,
        overall_growth_rate=round(overall_rate, 4),
        latest_mom_rate=round(latest_rate, 4),
        periods=len(input_data.series),
    )


def calculate_inventory_pressure(
    input_data: InventoryPressureInput,
) -> InventoryPressureOutput:
    if input_data.average_daily_sales <= 0:
        return InventoryPressureOutput(
            coverage_days=None,
            pressure="unknown",
            rationale="缺少有效日均销量，无法计算库存覆盖天数。",
        )
    coverage = (
        input_data.available_units + input_data.inbound_units
    ) / input_data.average_daily_sales
    if input_data.available_units == 0:
        pressure = "stockout"
    elif coverage < 21:
        pressure = "low"
    elif coverage <= 60:
        pressure = "healthy"
    elif coverage <= 120:
        pressure = "high"
    else:
        pressure = "overstock"
    return InventoryPressureOutput(
        coverage_days=round(coverage, 1),
        pressure=pressure,
        rationale=f"可用及在途库存预计覆盖 {coverage:.1f} 天。",
    )


def recommend_restock(input_data: RestockInput) -> RestockOutput:
    adjusted_daily_sales = input_data.average_daily_sales * max(0.5, 1 + input_data.growth_rate)
    planning_days = input_data.lead_time_days + input_data.safety_days
    target_days = max(input_data.target_coverage_days, planning_days)
    target_demand = round(adjusted_daily_sales * target_days)
    available_supply = input_data.available_units + input_data.inbound_units
    quantity = max(0, target_demand - available_supply)
    return RestockOutput(
        should_restock=quantity > 0,
        recommended_quantity=quantity,
        target_demand=target_demand,
        rationale=(
            f"按调整后日均销量 {adjusted_daily_sales:.2f}、目标 {target_days} 天需求，"
            f"扣除可用及在途 {available_supply} 件后计算。"
        ),
    )
