import itertools
from typing import TypedDict


class Ticket(TypedDict):
    id: str
    topic: str
    status: str


_tickets: dict[str, Ticket] = {}
_id_counter = itertools.count(1)


def create_ticket(topic: str) -> Ticket:
    ticket: Ticket = {"id": f"TCK-{next(_id_counter):04d}", "topic": topic, "status": "open"}
    _tickets[ticket["id"]] = ticket
    return ticket
