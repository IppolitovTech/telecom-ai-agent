from data.storage import save_uploaded_file
from models.upload import UploadResponse
from rag.ingest import ingest_file


def handle_upload(filename: str, content: bytes) -> UploadResponse:
    destination = save_uploaded_file(filename, content)
    ingest_file(destination)
    return UploadResponse(filename=destination.name, saved=True)
