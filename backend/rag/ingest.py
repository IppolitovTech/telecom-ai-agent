import logging
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import get_settings
from rag.embeddings import embed_passages
from rag.vector_store import get_collection

logger = logging.getLogger(__name__)

# multilingual-e5-small has no exact tokenizer wired in here, so chunk size is
# approximated in characters (~3 chars/token for RU text): 1800/250 chars
# lands in the target 500-800 token / 50-100 token overlap range from the roadmap.
_CHUNK_SIZE = 1800
_CHUNK_OVERLAP = 250

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=_CHUNK_SIZE,
    chunk_overlap=_CHUNK_OVERLAP,
    separators=["\n\n", "\n", ". ", " ", ""],
)


_TEXT_SUFFIXES = {".md", ".txt"}


def ingest_file(path: Path) -> int:
    if path.suffix.lower() not in _TEXT_SUFFIXES:
        # /api/upload accepts arbitrary files; only text/markdown knowledge
        # docs are indexable, so anything else is stored but not searched.
        return 0

    text = path.read_text(encoding="utf-8")
    chunks = _splitter.split_text(text)

    collection = get_collection()
    document = path.name
    collection.delete(where={"document": document})

    if not chunks:
        return 0

    ids = [f"{document}::{i}" for i in range(len(chunks))]
    metadatas = [{"document": document, "chunk": i} for i in range(len(chunks))]
    collection.add(
        ids=ids,
        embeddings=embed_passages(chunks),
        documents=chunks,
        metadatas=metadatas,
    )

    logger.info("ingest: %s -> %d chunks", document, len(chunks))
    return len(chunks)


def ingest_all() -> int:
    knowledge_dir = get_settings().knowledge_dir
    total = sum(ingest_file(path) for path in sorted(knowledge_dir.glob("*.md")))
    logger.info("ingest: %d chunks total", total)
    return total


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    ingest_all()
