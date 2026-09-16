from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: str


class ToolCall(BaseModel):
    name: str
    args: dict


class Source(BaseModel):
    document: str
    chunk: int
    score: float


class ChatResponse(BaseModel):
    reply: str
    tool_calls: list[ToolCall] = []
    sources: list[Source] = []
    error: bool = False
