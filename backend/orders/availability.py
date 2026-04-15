from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import HTTPException, status


MOSCOW_TZ = timezone(timedelta(hours=3), name="MSK")
ORDER_OPEN_HOUR = 8
ORDER_CLOSE_HOUR = 21


def is_order_time_open(now: Optional[datetime] = None) -> bool:
    current_time = now.astimezone(MOSCOW_TZ) if now else datetime.now(MOSCOW_TZ)
    return ORDER_OPEN_HOUR <= current_time.hour < ORDER_CLOSE_HOUR


def ensure_order_time_open() -> None:
    if is_order_time_open():
        return

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="\u0417\u0430\u043a\u0430\u0437\u044b \u043f\u0440\u0438\u043d\u0438\u043c\u0430\u044e\u0442\u0441\u044f \u0441 08:00 \u0434\u043e 21:00 \u043f\u043e \u043c\u043e\u0441\u043a\u043e\u0432\u0441\u043a\u043e\u043c\u0443 \u0432\u0440\u0435\u043c\u0435\u043d\u0438.",
    )
