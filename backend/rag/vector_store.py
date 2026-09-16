from functools import lru_cache

import chromadb
from chromadb import Collection

from config import get_settings

_COLLECTION_NAME = "knowledge"


@lru_cache
def get_collection() -> Collection:
    settings = get_settings()
    settings.chroma_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(settings.chroma_dir))
    # Embeddings are pre-normalized (embeddings.py), so cosine distance maps
    # directly to a 0..1 similarity score for the `sources` field (Stage 4).
    return client.get_or_create_collection(_COLLECTION_NAME, metadata={"hnsw:space": "cosine"})
