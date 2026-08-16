import calendar
import random
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.analytics import InventorySnapshot, Product, SalesFact

SIMULATION_SEED = 20260816
START_YEAR = 2025
START_MONTH = 3

PRODUCT_SPECS = [
    ("RACK-US-001", "龙门架", Decimal("699.00"), Decimal("360.00")),
    ("TREAD-US-001", "跑步机", Decimal("899.00"), Decimal("590.00")),
    ("DUMB-US-001", "哑铃套装", Decimal("129.00"), Decimal("112.00")),
    ("BENCH-US-001", "健身凳", Decimal("239.00"), Decimal("145.00")),
    ("CABLE-US-001", "拉力器", Decimal("189.00"), Decimal("105.00")),
]


def _month(index: int) -> tuple[int, int]:
    offset = START_MONTH - 1 + index
    return START_YEAR + offset // 12, offset % 12 + 1


def seed_demo_analytics(session: Session) -> None:
    if session.scalar(select(Product.id).limit(1)):
        return

    rng = random.Random(SIMULATION_SEED)
    products: dict[str, Product] = {}
    for sku, name, _, unit_cost in PRODUCT_SPECS:
        product = Product(
            sku=sku,
            name=name,
            category="健身器材",
            site="美国站",
            platform="Amazon",
            unit_cost=unit_cost,
        )
        session.add(product)
        products[sku] = product
    session.flush()

    for index in range(18):
        year, month = _month(index)
        sale_date = date(year, month, 1)
        snapshot_date = date(year, month, calendar.monthrange(year, month)[1])
        seasonal = 1.24 if month in {11, 12, 1} else 0.88 if month in {6, 7} else 1.0

        rack_units = 42 + index * 4 + rng.randint(-2, 2)
        treadmill_units = max(24, 92 - index * 4 + rng.randint(-3, 3))
        dumbbell_units = int((178 + rng.randint(-8, 8)) * seasonal)
        bench_units = int((68 + index + rng.randint(-4, 4)) * seasonal)
        cable_units = 76 + rng.randint(-5, 5)
        units_by_sku = {
            "RACK-US-001": rack_units,
            "TREAD-US-001": treadmill_units,
            "DUMB-US-001": dumbbell_units,
            "BENCH-US-001": bench_units,
            "CABLE-US-001": cable_units,
        }

        inventory_by_sku = {
            "RACK-US-001": (max(22, 175 - index * 9), 8, 20 if index > 14 else 0),
            "TREAD-US-001": (210 + index * 22, 12, 65),
            "DUMB-US-001": (300 + rng.randint(-20, 20), 24, 90),
            "BENCH-US-001": (145 + rng.randint(-15, 15), 10, 35),
            "CABLE-US-001": (120 + rng.randint(-10, 10), 7, 25),
        }

        for sku, _name, price, unit_cost in PRODUCT_SPECS:
            units = units_by_sku[sku]
            refund_rate = (
                Decimal("0.16") if sku == "CABLE-US-001" and index >= 15 else Decimal("0.03")
            )
            refund_units = int(Decimal(units) * refund_rate)
            session.add(
                SalesFact(
                    product_id=products[sku].id,
                    sale_date=sale_date,
                    units_sold=units,
                    revenue=(price * units).quantize(Decimal("0.01")),
                    cost=(unit_cost * units).quantize(Decimal("0.01")),
                    refund_units=refund_units,
                )
            )
            on_hand, reserved, inbound = inventory_by_sku[sku]
            session.add(
                InventorySnapshot(
                    product_id=products[sku].id,
                    snapshot_date=snapshot_date,
                    on_hand=on_hand,
                    reserved=reserved,
                    inbound=inbound,
                )
            )
    session.commit()
