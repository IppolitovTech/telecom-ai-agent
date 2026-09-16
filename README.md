# AI Support Agent for an ISP

A demo project showing how backend engineering experience carries over into building LLM
applications: an explicit (not black-box) agentic architecture with RAG, tool calling, and
orchestration through a router instead of LangChain's `AgentExecutor`.

The agent answers customer questions for an internet service provider, drawing on two data
sources:
- a knowledge base (tariffs, router setup, troubleshooting) via RAG search;
- internal tools (checking an order status, creating a support ticket) via explicit tool calling.

For complex requests where it isn't known upfront whether document search, a tool call, or
both will be needed, the agent uses a custom ReAct loop with a hard iteration limit,
implemented without third-party agent frameworks.

## Running locally

Backend (from `backend/`, with the virtual environment activated):

```powershell
uvicorn main:app --reload
```

Frontend (from `frontend/`):

```powershell
npm run dev
```

## Language

- All code — identifiers, comments, commit messages, error messages,
  log strings — must be written in English.
- The only exception is documentation under `docs/ru/` (vision,
  architecture, roadmap, ADRs), which stays in Russian.
