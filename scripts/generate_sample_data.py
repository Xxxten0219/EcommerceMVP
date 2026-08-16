#!/usr/bin/env python3
"""Generate deterministic CSV fixtures for the sales import demo."""

import csv
import random
from datetime import date
from decimal import Decimal
from pathlib import Path

SEED = 20260816
OUTPUT = (
    Path(__file__).resolve().parents[1] / "data" / "samples" / "sales_import_demo.csv"
)


def generate() -> None:
    rng = random.Random(SEED)
    rows = []
    products = [
        ("RACK-DEMO-001", "龙门架", "699.00", "360.00"),
        ("BENCH-DEMO-001", "健身凳", "239.00", "145.00"),
    ]
    for month in range(1, 7):
        for sku, name, price_text, cost_text in products:
            units = (38 + month * 5 if "RACK" in sku else 70 - month * 3) + rng.randint(
                -2, 2
            )
            price = Decimal(price_text)
            cost = Decimal(cost_text)
            rows.append(
                {
                    "sale_date": date(2026, month, 1).isoformat(),
                    "sku": sku,
                    "product_name": name,
                    "category": "健身器材",
                    "site": "美国站",
                    "platform": "Amazon",
                    "units_sold": units,
                    "revenue": price * units,
                    "cost": cost * units,
                    "refund_units": 1,
                }
            )

    rows.extend(
        [
            {**rows[0]},
            {**rows[1], "sale_date": "2026-99-01"},
            {**rows[2], "revenue": "not-a-number"},
            {**rows[3], "sku": ""},
        ]
    )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8-sig", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    generate()
