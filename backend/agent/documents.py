import logging

from data.storage import save_uploaded_file
from models.upload import UploadResponse
from rag.ingest import ingest_file

logger = logging.getLogger(__name__)


def handle_upload(filename: str, content: bytes) -> UploadResponse:
    destination = save_uploaded_file(filename, content)
    chunks = ingest_file(destination)
    logger.info("documents: %s -> %s, indexed %d chunks", filename, destination, chunks)
    return UploadResponse(filename=destination.name, saved=True)
