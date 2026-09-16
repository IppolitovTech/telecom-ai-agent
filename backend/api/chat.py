from fastapi import APIRouter

from agent.router import handle_chat
from models.chat import ChatRequest, ChatResponse

router = APIRouter()


@router.post("/api/chat")
def chat(request: ChatRequest) -> ChatResponse:
    return handle_chat(request)
