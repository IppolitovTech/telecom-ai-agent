# CLAUDE.md

Rules for Claude Code work in this repository. See [docs/ru/ARCHITECTURE.md](docs/ru/ARCHITECTURE.md) and [docs/ru/ROADMAP.md](docs/ru/ROADMAP.md) for the overall design and stages.

## Monorepo: backend / frontend stay separate

- `backend/` and `frontend/` are independent projects. No shared code imports between them.
- The contract between them is HTTP JSON only, per the schema in `backend/models/` (see the response shape in ARCHITECTURE.md, ROADMAP Stage 4). If the shape of the `/api/chat` response changes, update the Pydantic schema in `models/` first, then the frontend type in sync.
- Each side gets its own `CLAUDE.md` (`backend/CLAUDE.md`, `frontend/CLAUDE.md`) with layer-level detail. This file only covers the boundary between them and repo-wide rules.

## Backend: dependency direction (a rule, not just a folder layout)

```
api/  →  agent/  →  rag/ , data/
         (business logic)   (retrieval, storage)
```

Dependencies flow one way, top to bottom. A lower layer never imports a higher one and never knows about HTTP.

- **`api/`** (`chat.py`, `upload.py`) — thin route layer. Only: parse the request (via a Pydantic model from `models/`), call a function in `agent/`, return the response. No business logic, no direct access to the vector store or the order "DB" inside a route.
- **`agent/`** (`router.py`, `tools.py`, `prompts.py`) — business logic and orchestration: intent classification, the ReAct loop, branch selection, assembling the final answer. Contains no FastAPI `Request`/`Response` objects and never reads/writes data directly — only through functions in `rag/` and `data/`.
- **`rag/`** (`embeddings.py`, `ingest.py`, `retriever.py`) — pure functions around vector search. Knows nothing about the router/intent, knows nothing about HTTP.
- **`data/`** — CRUD and fake/test data, pulled out of `agent/tools.py`: access to "orders" (`check_order_status`), ticket creation (`create_ticket`), file storage from `upload.py`. `agent/tools.py` calls functions in `data/` rather than holding the data/dicts itself. This separates "what the function does as a business operation" (`agent/tools.py`) from "how and where the data is stored" (`data/`) — even while `data/` is just in-memory dicts/stubs at the pet-project stage.
- **`models/`** — Pydantic request/response schemas only (the I/O contract). Not to be confused with ORM data models — the project deliberately has none of those (see "What we deliberately skip" in ROADMAP).

Practical implication: if you're editing an endpoint and reach for an `if` with a business condition directly in `api/chat.py`, that's a signal the logic belongs in `agent/`. If `agent/tools.py` accumulates dicts of fake orders, they belong in `data/`.

## Frontend: the same separation

- The API client (fetch calls to `/api/chat`, `/api/upload`) lives apart from components, not inside JSX.
- Components are presentation only (chat, "Agent activity", the sources list — see ROADMAP Stage 5). `session_id`/localStorage logic lives in a separate hook, not in a component.

## Implementation invariants

- **Async & threadpool.** Heavy CPU/IO calls (embedding generation, ChromaDB) run synchronously via `run_in_threadpool` / `anyio.to_thread.run_sync`, or the route is declared as `def`, so the event loop never blocks.
- **Prefixes for `multilingual-e5-small`.** Required: `passage: ` at indexing time (`rag/ingest.py`) and `query: ` at search time (`rag/retriever.py`). Skipping them silently degrades search quality — this isn't optional, it's a model requirement.
- **Error contract.** On any LLM or external-service failure, `/api/chat` must return valid JSON per the Pydantic schema (with an error flag and a neutral user-facing message), not a 500 Internal Server Error. Consistent with the Stage 4 rule that the response shape doesn't change based on scenario.
- **Config only through `pydantic-settings`.** Keys, paths, model names are read through `Settings`. Direct `os.getenv` calls in code are not allowed.

## MVP boundaries

Don't propose or add anything listed under "What we deliberately skip" in ROADMAP.md (auth, Kubernetes, Redis/Postgres for memory, Celery/Kafka, streaming, multi-agent, etc.) unless explicitly asked.
