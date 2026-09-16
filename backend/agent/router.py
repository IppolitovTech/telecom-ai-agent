import json
import logging
import time
from typing import Literal

from pydantic import BaseModel, Field

from agent.llm import get_llm
from agent.prompts import (
    CLASSIFIER_SYSTEM_PROMPT,
    REACT_SYSTEM_PROMPT,
    SYNTHESIS_SYSTEM_PROMPT,
    format_history,
)
from agent.tools import ToolName, call_tool
from data.memory import append_turn, get_history
from models.chat import ChatRequest, ChatResponse, Source, ToolCall
from rag.retriever import RetrievedChunk, retrieve

logger = logging.getLogger(__name__)

# Hard cap on think -> act -> observe iterations for the `combined` branch —
# protects against the model looping instead of ever reaching final_answer.
MAX_REACT_ITERATIONS = 3


def _log(event: str, session_id: str, **fields: object) -> None:
    logger.info(json.dumps({"event": event, "session_id": session_id, **fields}, ensure_ascii=False))


class IntentClassification(BaseModel):
    intent: Literal["rag_search", "tool_call", "direct_answer", "combined"]
    tool_name: ToolName | None = Field(default=None, description="Требуется, если intent = tool_call")
    tool_args: dict = Field(default_factory=dict, description="Аргументы инструмента, напр. {'order_id': '12345'}")
    search_query: str | None = Field(default=None, description="Поисковый запрос, если intent = rag_search")


class ReactStep(BaseModel):
    action: Literal["rag_search", "tool_call", "final_answer"]
    search_query: str | None = None
    tool_name: ToolName | None = None
    tool_args: dict = Field(default_factory=dict)
    answer: str | None = Field(default=None, description="Текст финального ответа, если action = final_answer")


def _classify_intent(message: str, history: list[dict]) -> IntentClassification:
    llm = get_llm().with_structured_output(IntentClassification)
    prompt = (
        f"{CLASSIFIER_SYSTEM_PROMPT}\n\n"
        f"История диалога:\n{format_history(history)}\n\n"
        f"Сообщение пользователя: {message}"
    )
    return llm.invoke(prompt)


def _decide_next_step(message: str, history: list[dict], scratchpad: list[dict]) -> ReactStep:
    llm = get_llm().with_structured_output(ReactStep)
    scratchpad_text = (
        "\n".join(
            f"Шаг {i + 1}: действие={step['action']}, вход={step['input']!r}\nРезультат: {step['observation']}"
            for i, step in enumerate(scratchpad)
        )
        or "(шагов ещё не было)"
    )
    prompt = (
        f"{REACT_SYSTEM_PROMPT}\n\n"
        f"История диалога:\n{format_history(history)}\n\n"
        f"Сообщение пользователя: {message}\n\n"
        f"Scratchpad:\n{scratchpad_text}"
    )
    return llm.invoke(prompt)


def _synthesize(session_id: str, message: str, history: list[dict], context: str) -> str:
    # Same provider-switchable get_llm() as classification/ReAct, not a hardcoded
    # ChatAnthropic — keeps the single .env switch point from Stage 1 (no special
    # case in agent/), even for the final synthesis call.
    llm = get_llm()
    prompt = (
        f"{SYNTHESIS_SYSTEM_PROMPT}\n\n"
        f"История диалога:\n{format_history(history)}\n\n"
        f"Сообщение пользователя: {message}\n\n"
        f"Контекст:\n{context}"
    )
    start = time.perf_counter()
    reply = str(llm.invoke(prompt).content)
    llm_ms = round((time.perf_counter() - start) * 1000)
    _log("synthesis", session_id, llm_ms=llm_ms)
    return reply


def _sources_from_chunks(chunks: list[RetrievedChunk]) -> list[Source]:
    return [Source(document=c.document, chunk=c.chunk, score=round(c.score, 4)) for c in chunks]


def _run_rag_search(session_id: str, query: str) -> tuple[str, list[Source]]:
    start = time.perf_counter()
    chunks = retrieve(query)
    retrieval_ms = round((time.perf_counter() - start) * 1000)
    _log("retrieval", session_id, query=query, hits=len(chunks), retrieval_ms=retrieval_ms)

    if not chunks:
        return "Поиск по базе знаний не дал результатов.", []

    context = "\n\n".join(f"[{c.document}, чанк {c.chunk}]\n{c.text}" for c in chunks)
    return context, _sources_from_chunks(chunks)


def _run_tool_call(session_id: str, tool_name: ToolName, tool_args: dict) -> tuple[str, ToolCall]:
    start = time.perf_counter()
    result = call_tool(tool_name, tool_args)
    tool_ms = round((time.perf_counter() - start) * 1000)
    _log("tool_call", session_id, tool_name=tool_name, tool_args=tool_args, tool_ms=tool_ms)
    return result, ToolCall(name=tool_name, args=tool_args)


def _run_react_loop(
    session_id: str, message: str, history: list[dict]
) -> tuple[str, list[ToolCall], list[Source]]:
    scratchpad: list[dict] = []
    tool_calls: list[ToolCall] = []
    sources: list[Source] = []

    for iteration in range(1, MAX_REACT_ITERATIONS + 1):
        start = time.perf_counter()
        step = _decide_next_step(message, history, scratchpad)
        llm_ms = round((time.perf_counter() - start) * 1000)
        _log("react_step", session_id, iteration=iteration, action=step.action, llm_ms=llm_ms)

        if step.action == "final_answer":
            return step.answer or "Не удалось сформировать ответ.", tool_calls, sources

        if step.action == "rag_search":
            query = step.search_query or message
            context, new_sources = _run_rag_search(session_id, query)
            sources.extend(new_sources)
            scratchpad.append({"action": "rag_search", "input": query, "observation": context})
        elif step.action == "tool_call" and step.tool_name:
            result, tool_call = _run_tool_call(session_id, step.tool_name, step.tool_args)
            tool_calls.append(tool_call)
            scratchpad.append(
                {
                    "action": "tool_call",
                    "input": {"tool": step.tool_name, "args": step.tool_args},
                    "observation": result,
                }
            )
        else:
            # Malformed step (e.g. tool_call without tool_name) — record and move
            # on instead of crashing or repeating the same bad step forever.
            scratchpad.append(
                {"action": step.action, "input": None, "observation": "Действие пропущено: некорректные параметры."}
            )

    # Hit the hard iteration limit without a final_answer — force a synthesis
    # from whatever context was gathered so the loop always terminates.
    context = "\n\n".join(f"Шаг {i + 1} ({s['action']}): {s['observation']}" for i, s in enumerate(scratchpad))
    reply = _synthesize(session_id, message, history, context or "Контекст не собран.")
    return reply, tool_calls, sources


def handle_chat(request: ChatRequest) -> ChatResponse:
    session_id = request.session_id
    message = request.message
    history = get_history(session_id)
    request_start = time.perf_counter()

    try:
        start = time.perf_counter()
        classification = _classify_intent(message, history)
        llm_ms = round((time.perf_counter() - start) * 1000)
        _log("intent_classified", session_id, intent=classification.intent, llm_ms=llm_ms)

        tool_calls: list[ToolCall] = []
        sources: list[Source] = []

        if classification.intent == "direct_answer":
            reply = _synthesize(session_id, message, history, "(поиск и инструменты не использовались)")

        elif classification.intent == "rag_search":
            query = classification.search_query or message
            context, sources = _run_rag_search(session_id, query)
            reply = _synthesize(session_id, message, history, context)

        elif classification.intent == "tool_call" and classification.tool_name:
            result, tool_call = _run_tool_call(session_id, classification.tool_name, classification.tool_args)
            tool_calls = [tool_call]
            reply = _synthesize(session_id, message, history, result)

        else:  # combined, or a malformed tool_call classification missing tool_name
            reply, tool_calls, sources = _run_react_loop(session_id, message, history)

        append_turn(session_id, "user", message)
        append_turn(session_id, "assistant", reply)
        total_ms = round((time.perf_counter() - request_start) * 1000)
        _log("chat_completed", session_id, intent=classification.intent, total_ms=total_ms)
        return ChatResponse(reply=reply, tool_calls=tool_calls, sources=sources)

    except Exception:
        total_ms = round((time.perf_counter() - request_start) * 1000)
        logger.error(
            json.dumps({"event": "chat_failed", "session_id": session_id, "total_ms": total_ms}, ensure_ascii=False),
            exc_info=True,
        )
        return ChatResponse(
            reply="Извините, произошла временная ошибка. Попробуйте, пожалуйста, ещё раз чуть позже.",
            error=True,
        )
