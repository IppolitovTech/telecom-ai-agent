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

## Architecture

```
                  ┌──────────────┐
                  │ User message │
                  └──────┬───────┘
                         ▼
                  ┌──────────────┐
                  │ Router/Agent │  ← decides: RAG search, a tool call, or a direct answer
                  └──────┬───────┘
                         │
             ┌───────────┼────────────┐
             ▼           ▼            ▼
        RAG search   Tool call   Direct answer
             │           │
             └─────┬─────┘
                   ▼
             ┌────────────┐
             │ Final LLM  │  ← synthesizes retrieved context / tool result into a reply
             └─────┬──────┘
                   ▼
        structured response { reply, tool_calls, sources }
```

See [docs/ru/ARCHITECTURE.md](docs/ru/ARCHITECTURE.md) for the full design (in Russian) and
[docs/ru/ROADMAP.md](docs/ru/ROADMAP.md) for how the project was built stage by stage.

## Stack

- **Backend:** FastAPI, LangChain core (`ChatOpenAI` pointed at OpenRouter, or `ChatAnthropic` —
  the two interchangeable LLM providers, switched only via `LLM_PROVIDER` in `.env`), ChromaDB
  as the vector store, `sentence-transformers` with `intfloat/multilingual-e5-small` for
  embeddings.
- **Frontend:** React 19 + TypeScript, Vite.
- **Infra:** Docker Compose (backend + frontend containers, HuggingFace cache and Chroma data
  as named volumes), GitHub Actions CI (lint + evaluation run on every push and pull request
  targeting `main`).

## Running locally

### Docker Compose

```bash
cp backend/.env.example backend/.env   # fill in OPENROUTER_API_KEY or ANTHROPIC_API_KEY
docker compose up
```

Backend: http://localhost:8000, frontend: http://localhost:5173.

### Manually

Backend (from `backend/`, with the virtual environment activated):

```powershell
pip install -r requirements.txt
uvicorn main:app --reload
```

Frontend (from `frontend/`):

```powershell
npm install
npm run dev
```

## Evaluation

`evaluation/run.py` checks two things against `evaluation/questions.json`: whether
`retriever.retrieve()` returns the expected source document for in-domain questions, and
whether the agent avoids citing a source for out-of-domain ones instead of fabricating one.

Latest run against the bundled `knowledge/` corpus:

```
Questions: 10
Correct source retrieved: 10/10
Retrieval accuracy: 100%
```

## Use of AI assistants

This project was built with Claude Code as a pair-programming assistant throughout —
architecture decisions, implementation, and this documentation. Commits after the initial
commit carry a `Co-Authored-By: Claude` trailer in the git history.
