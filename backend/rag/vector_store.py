import logging
from functools import lru_cache

import chromadb
from chromadb import Collection

from config import get_settings

logger = logging.getLogger(__name__)

_COLLECTION_NAME = "knowledge"


@lru_cache
def get_collection() -> Collection:
    settings = get_settings()
    settings.chroma_dir.mkdir(parents=True, exist_ok=True)
    logger.info("vector_store: connecting to Chroma at %s", settings.chroma_dir)
    client = chromadb.PersistentClient(path=str(settings.chroma_dir))
    # Embeddings are pre-normalized (embeddings.py), so cosine distance maps
    # directly to a 0..1 similarity score for the `sources` field (Stage 4).
    collection = client.get_or_create_collection(_COLLECTION_NAME, metadata={"hnsw:space": "cosine"})
    logger.info("vector_store: collection '%s' ready, %d items", _COLLECTION_NAME, collection.count())
    return collection
