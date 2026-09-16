from typing import TypedDict


class Order(TypedDict):
    status: str
    eta: str | None
    technician: str | None


# Fixed fake dataset — pet-project stub, per ROADMAP Stage 3 ("check_order_status —
# заглушка с фиктивными данными"). Real implementation would query an order system.
_FAKE_ORDERS: dict[str, Order] = {
    "12345": {"status": "scheduled", "eta": "2026-09-18", "technician": "Иван Петров"},
    "67890": {"status": "completed", "eta": None, "technician": None},
    "11111": {"status": "in_progress", "eta": "2026-09-17", "technician": "Анна Сидорова"},
}


def get_order(order_id: str) -> Order | None:
    return _FAKE_ORDERS.get(order_id)
