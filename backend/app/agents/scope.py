import calendar
from datetime import date

PRODUCT_NAMES = ["龙门架", "跑步机", "哑铃", "健身凳", "拉力器"]


def _month_start(value: date) -> date:
    return value.replace(day=1)


def _shift_month(value: date, offset: int) -> date:
    month_index = value.year * 12 + value.month - 1 + offset
    return date(month_index // 12, month_index % 12 + 1, 1)


def resolve_scope(text: str, previous: dict[str, str] | None = None) -> dict[str, str]:
    today = date.today()
    scope = dict(previous or {})
    scope.setdefault("site", "美国站")
    scope.setdefault("platform", "Amazon")
    scope.setdefault("category", "健身器材")
    scope.setdefault("granularity", "month")

    for name in PRODUCT_NAMES:
        if name in text:
            scope["product_name"] = name
            break

    if "上个月" in text:
        start = _shift_month(_month_start(today), -1)
        end = date(start.year, start.month, calendar.monthrange(start.year, start.month)[1])
    elif "本月" in text:
        start = _month_start(today)
        end = today
    elif "18个月" in text or "十八个月" in text:
        start = _shift_month(_month_start(today), -17)
        end = today
    else:
        start = _shift_month(_month_start(today), -5)
        end = today

    scope["start_date"] = start.isoformat()
    scope["end_date"] = end.isoformat()
    return scope
