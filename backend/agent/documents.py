from data.storage import save_uploaded_file
from models.upload import UploadResponse


def handle_upload(filename: str, content: bytes) -> UploadResponse:
    destination = save_uploaded_file(filename, content)
    return UploadResponse(filename=destination.name, saved=True)
