from dataclasses import dataclass

from config import get_settings
from rag.embeddings import embed_query
from rag.vector_store import get_collection


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
        return []

    result = collection.query(
        query_embeddings=[embed_query(query)],
        n_results=min(k or get_settings().retrieval_k, count),
    )

    return [
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
