from contextlib import asynccontextmanager

import anyio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.chat import router as chat_router
from api.upload import router as upload_router
from config import get_settings
from rag.ingest import ingest_all


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once at startup, not per-request — reindexing on every chat call
    # would make server start (and each restart) pay embedding cost repeatedly.
    await anyio.to_thread.run_sync(ingest_all)
    yield


app = FastAPI(title="AI Support Agent", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(upload_router)
