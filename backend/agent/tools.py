import logging
from collections.abc import Callable
from typing import Literal

from data.orders import get_order
from data.tickets import create_ticket as create_ticket_record

logger = logging.getLogger(__name__)

ToolName = Literal["check_order_status", "create_ticket"]

_STATUS_LABELS = {
    "scheduled": "запланирована",
    "in_progress": "выполняется",
    "completed": "выполнена",
}


def check_order_status(order_id: str) -> str:
    order = get_order(order_id)
    if order is None:
        logger.warning("tools: order %r not found", order_id)
        return f"Заявка с номером {order_id} не найдена."

    label = _STATUS_LABELS.get(order["status"], order["status"])
    parts = [f"Заявка {order_id}: статус — {label}."]
    if order["eta"]:
        parts.append(f"Плановая дата: {order['eta']}.")
    if order["technician"]:
        parts.append(f"Назначен специалист: {order['technician']}.")
    return " ".join(parts)


def create_ticket(topic: str) -> str:
    ticket = create_ticket_record(topic)
    logger.info("tools: created ticket %s for topic %r", ticket["id"], topic)
    return f"Тикет {ticket['id']} создан по теме «{topic}»."


TOOLS: dict[ToolName, Callable[..., str]] = {
    "check_order_status": check_order_status,
    "create_ticket": create_ticket,
}

TOOL_ARG_NAMES: dict[ToolName, str] = {
    "check_order_status": "order_id",
    "create_ticket": "topic",
}


def call_tool(tool_name: ToolName, tool_args: dict) -> str:
    arg_name = TOOL_ARG_NAMES[tool_name]
    arg_value = tool_args.get(arg_name, "")
    if not arg_value:
        logger.warning("tools: %s called without %r in args=%r", tool_name, arg_name, tool_args)
    return TOOLS[tool_name](arg_value)
