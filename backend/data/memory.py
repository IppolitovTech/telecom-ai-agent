from collections import defaultdict
from typing import Literal, TypedDict


class Turn(TypedDict):
    role: Literal["user", "assistant"]
    content: str


# In-memory dict, resets on restart — an explicit, documented trade-off for a
# pet project (ROADMAP Stage 3), not a stand-in for Redis/Postgres.
_MAX_TURNS = 10
_history: dict[str, list[Turn]] = defaultdict(list)


def get_history(session_id: str) -> list[Turn]:
    return list(_history[session_id])


def append_turn(session_id: str, role: Literal["user", "assistant"], content: str) -> None:
    turns = _history[session_id]
    turns.append({"role": role, "content": content})
    del turns[: max(0, len(turns) - _MAX_TURNS)]
