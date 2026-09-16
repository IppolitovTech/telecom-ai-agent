import logging
from dataclasses import dataclass

from config import get_settings
from rag.embeddings import embed_query
from rag.vector_store import get_collection

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    document: str
    chunk: int
    score: float
    text: str


def retrieve(query: str, k: int | None = None) -> list[RetrievedChunk]:
    collection = get_collection()
    count = collection.count()
    if count == 0:
        logger.warning("retriever: collection is empty, skipping search for %r", query)
        return []

    result = collection.query(
        query_embeddings=[embed_query(query)],
        n_results=min(k or get_settings().retrieval_k, count),
    )

    chunks = [
        RetrievedChunk(
            document=metadata["document"],
            chunk=metadata["chunk"],
            score=1 - distance,
            text=text,
        )
        for text, metadata, distance in zip(
            result["documents"][0], result["metadatas"][0], result["distances"][0]
        )
    ]
    logger.info(
        "retriever: query=%r hits=%d results=%s",
        query,
        len(chunks),
        [(c.document, c.chunk, round(c.score, 4)) for c in chunks],
    )
    return chunks
