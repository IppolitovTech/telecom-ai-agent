from models.chat import ChatRequest, ChatResponse


def handle_chat(request: ChatRequest) -> ChatResponse:
    # No intent classification yet — placeholder so the endpoint contract is testable.
    return ChatResponse(reply=f"Echo: {request.message}")
