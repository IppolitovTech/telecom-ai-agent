from pathlib import Path

from config import get_settings


def save_uploaded_file(filename: str, content: bytes) -> Path:
    knowledge_dir = get_settings().knowledge_dir
    knowledge_dir.mkdir(parents=True, exist_ok=True)

    destination = knowledge_dir / Path(filename).name
    destination.write_bytes(content)
    return destination
